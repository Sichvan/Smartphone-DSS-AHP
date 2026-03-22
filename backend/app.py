import os
import sys
import numpy as np
from flask import Flask, render_template, request, jsonify

# BẮT BUỘC PHẢI CÓ DÒNG NÀY TRƯỚC KHI IMPORT TỪ BACKEND / AI_ENGINE
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Giờ mới import an toàn
from ai_engine.ai_adapter import AIAdapter
from backend.ahp_core import AHP
from backend.database import init_history_table, save_history, get_user_history, clear_user_history

app = Flask(__name__, static_folder='../frontend', static_url_path='', template_folder='../frontend')
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mobiles.csv'))

init_history_table()
ai = AIAdapter()
ahp = AHP(data_path=DATA_PATH)

RI_TABLE = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12}

def calculate_ahp_weights(matrix):
    matrix = np.array(matrix)
    n = len(matrix)
    if n == 0: return [], 0
    col_sums = matrix.sum(axis=0)
    norm_matrix = matrix / col_sums
    weights = norm_matrix.mean(axis=1)
    
    aw = matrix.dot(weights)
    lambda_max = np.mean(aw / weights)
    ci = (lambda_max - n) / (n - 1) if n > 1 else 0
    ri = RI_TABLE.get(n, 1.45)
    cr = ci / ri if ri > 0 else 0
    return weights.tolist(), cr

def get_phone_metric(phone, criterion):
    """Trích xuất giá trị dựa trên các key từ AHP Core"""
    try:
        if criterion == "Giá":
            # Giá thấp là tốt
            return float(phone.get('Price_USD', 999))
        elif criterion == "Hiệu năng":
            # Kết hợp RAM và điểm CPU
            return float(phone.get('RAM_val', 0)) * 0.5 + float(phone.get('Proc_score', 0)) * 0.5
        elif criterion == "Camera":
            return float(phone.get('Back_MP', 0)) * 0.7 + float(phone.get('Front_MP', 0)) * 0.3
        elif criterion == "Trải nghiệm":
            battery = float(phone.get('Battery_val', 0)) / 1000
            screen = float(phone.get('Screen_val', 0))
            weight_inv = 200 / float(phone.get('Weight_val', 200))
            return (battery * 0.4) + (screen * 0.3) + (weight_inv * 0.3)
    except:
        return 1.0
    return 1.0

def build_phone_comparison_matrix(phones, criterion):
    n = len(phones)
    matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            val_i = get_phone_metric(phones[i], criterion)
            val_j = get_phone_metric(phones[j], criterion)
            
            # Logic so sánh AHP tự động (V_i / V_j)
            if criterion == "Giá":
                # Nghịch đảo: Máy i rẻ hơn máy j (val_i < val_j) thì ratio > 1
                ratio = val_j / val_i if val_i > 0 else 1
            else:
                ratio = val_i / val_j if val_j > 0 else 1
            
            # Giới hạn tỷ lệ theo thang đo AHP 1-9
            if ratio > 9: ratio = 9
            if ratio < 1/9: ratio = 1/9
            matrix[i][j] = ratio
    return matrix

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    user_text = request.json.get('text', '')
    criteria_keys = ["Giá", "Hiệu năng", "Trải nghiệm", "Camera"]
    
    # BƯỚC 1: Sàng lọc top 5
    weights_dict = ai.get_weights(user_text)
    top_5_candidates = ahp.rank_phones(weights_dict) 
    
    if not top_5_candidates:
        return jsonify({"status": "error", "message": "Không có dữ liệu."})

    phone_names = [p.get('Model Name', 'Unknown') for p in top_5_candidates]

    # BƯỚC 2: Tính toán AHP chi tiết
    ahp_steps = []
    
    # 2.1. Ma trận tiêu chí (4x4)
    c_matrix = [[weights_dict[k1]/weights_dict[k2] for k2 in criteria_keys] for k1 in criteria_keys]
    c_weights, c_cr = calculate_ahp_weights(c_matrix)
    ahp_steps.append({
        "step_name": "Phân tích mức độ ưu tiên tiêu chí",
        "labels": criteria_keys,
        "matrix": c_matrix,
        "weights": c_weights,
        "cr": c_cr,
        "explanation": f"Hệ thống xác định bạn ưu tiên nhất vào: {max(weights_dict, key=weights_dict.get)}"
    })

    # 2.2. Ma trận phương án cho từng tiêu chí (5x5)
    phone_weights_by_crit = {}
    for crit in criteria_keys:
        p_matrix = build_phone_comparison_matrix(top_5_candidates, crit)
        p_weights, p_cr = calculate_ahp_weights(p_matrix)
        phone_weights_by_crit[crit] = p_weights
        
        best_phone = phone_names[np.argmax(p_weights)]
        ahp_steps.append({
            "step_name": f"So sánh 5 máy về: {crit}",
            "labels": phone_names,
            "matrix": p_matrix.tolist(),
            "weights": p_weights,
            "cr": p_cr,
            "explanation": f"Về {crit}, mẫu {best_phone} thể hiện tốt nhất."
        })

    # BƯỚC 3: Tổng hợp điểm cuối cùng
    final_ranked_list = []
    for idx, phone in enumerate(top_5_candidates):
        # Điểm AHP = Tổng (Trọng số tiêu chí * Trọng số máy trong tiêu chí đó)
        final_score = sum(c_weights[i] * phone_weights_by_crit[criteria_keys[i]][idx] for i in range(4))
        
        # Tạo object gọn gàng gửi về Frontend
        final_ranked_list.append({
            "Model Name": phone['Model Name'],
            "Price_USD": phone['Price_USD'],
            "RAM_val": phone['RAM_val'],
            "Battery_val": phone['Battery_val'],
            "Back_MP": phone['Back_MP'],
            "final_ahp_score": round(final_score, 4)
        })

    final_ranked_list = sorted(final_ranked_list, key=lambda x: x['final_ahp_score'], reverse=True)
    
    # Lưu lịch sử
    save_history(user_text, final_ranked_list)

    return jsonify({
        "status": "success",
        "initial_candidates": top_5_candidates,
        "ahp_steps": ahp_steps,
        "final_ranking": final_ranked_list
    })

@app.route('/history', methods=['GET'])
def history():
    return jsonify({"status": "success", "history": get_user_history()})

@app.route('/history', methods=['DELETE'])
def clear_history():
    success = clear_user_history()
    if success:
        return jsonify({"status": "success", "message": "Đã xóa lịch sử."})
    return jsonify({"status": "error", "message": "Không thể xóa."}), 500
if __name__ == '__main__':
    app.run(debug=True, port=5000)
    
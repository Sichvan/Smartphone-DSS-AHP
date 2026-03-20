import os
import sys
import random
from flask import Flask, render_template, request, jsonify

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ai_engine.ai_adapter import AIAdapter
from backend.ahp_core import AHP

# Import database
from backend.database import init_history_table, save_history, get_user_history

app = Flask(__name__, static_folder='../frontend', static_url_path='', template_folder='../frontend')
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mobiles.csv'))

# Khởi tạo bảng lịch sử trong DB
init_history_table()

ai = AIAdapter()
ahp = AHP(data_path=DATA_PATH)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    user_text = request.json.get('text', '')
    
    # ==========================================
    # 1. GỌI AI THẬT ĐỂ LẤY TRỌNG SỐ
    # ==========================================
    try:
        # Gọi thẳng hàm get_weights từ AIAdapter của bạn
        weights = ai.get_weights(user_text)
        print(f"[+] AI đã phân tích thành công: {weights}")
    except Exception as e:
        print(f"[-] Lỗi gọi AI (Dùng trọng số đều): {e}")
        weights = {"Giá": 0.25, "Hiệu năng": 0.25, "Trải nghiệm": 0.25, "Camera": 0.25}

    # ==========================================
    # 2. DỊCH NGƯỢC MA TRẬN 4x4 TỪ TRỌNG SỐ AI
    # (Để hiển thị lên giao diện Web cho đúng chuẩn AHP)
    # ==========================================
    criteria_keys = ["Giá", "Hiệu năng", "Trải nghiệm", "Camera"]
    ai_matrix = []
    
    for i in range(4):
        row = []
        for j in range(4):
            # Công thức toán học: Phần tử A(i,j) = Trọng_số(i) / Trọng_số(j)
            weight_i = weights[criteria_keys[i]]
            weight_j = weights[criteria_keys[j]]
            
            # Tránh chia cho 0
            val = weight_i / weight_j if weight_j > 0 else 1.0
            row.append(val)
        ai_matrix.append(row)

    # ==========================================
    # 3. CHẠY AHP LẤY TOP 10 & TOP 5
    # ==========================================
    top_10 = ahp.rank_phones(weights)

    if not top_10:
        return jsonify({"status": "error", "message": "Không có dữ liệu điện thoại."})

    candidates = top_10.copy()
    random.shuffle(candidates) 
    
    top_5_ranking = top_10[:5] 

    # ==========================================
    # 4. LƯU LỊCH SỬ VÀO POSTGRESQL
    # ==========================================
    save_history(user_text, top_5_ranking)

    # Tạo câu giải thích XAI (Explainable AI)
    top_criterion = max(weights, key=weights.get)
    explanation = f"Từ dữ liệu của AI, hệ thống tính toán bạn ưu tiên **{top_criterion}** nhất ({weights[top_criterion]*100:.1f}%)."

    return jsonify({
        "status": "success",
        "matrix": ai_matrix,
        "weights": weights,
        "candidates": candidates,  
        "ranking": top_5_ranking,  
        "explanation": explanation
    })

# ==========================================
# API TRẢ VỀ LỊCH SỬ CHO FRONTEND
# ==========================================
@app.route('/history', methods=['GET'])
def history():
    data = get_user_history()
    return jsonify({
        "status": "success",
        "history": data
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
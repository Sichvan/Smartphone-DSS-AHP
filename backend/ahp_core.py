import pandas as pd
import re
import csv

class AHP:
    def __init__(self, data_path):
        try:
            # =========================================================
            # THUẬT TOÁN ĐỌC CSV "XUYÊN GIÁP" (Phá lớp bọc ngoặc kép của Excel)
            # =========================================================
            with open(data_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                raw_data = list(reader)

            processed_data = []
            for row in raw_data:
                if not row: continue
                # Nếu phát hiện cả dòng bị nhồi nhét vào 1 cột duy nhất
                if len(row) == 1 and ',' in row[0]:
                    # Phân giải lại chuỗi bên trong nó
                    inner_reader = csv.reader([row[0]])
                    processed_data.append(next(inner_reader))
                else:
                    processed_data.append(row)

            if processed_data:
                headers = [str(h).strip() for h in processed_data[0]] # Lấy tiêu đề
                self.df = pd.DataFrame(processed_data[1:], columns=headers)
                print("\n[+] Đã phá giải thành công lớp bọc lỗi của file CSV!")
                print(f"[*] Số dòng thô đọc được: {len(self.df)}")
            else:
                self.df = pd.DataFrame()
                
        except Exception as e:
            print(f"\n[-] Lỗi đọc file CSV: {e}")
            self.df = pd.DataFrame()
            
        self._clean_data()

    def _clean_data(self):
        df = self.df.copy()
        
        def find_col(possible_names):
            for name in possible_names:
                if name in df.columns:
                    return name
            return None

        def safe_extract(col_name):
            if col_name:
                return df[col_name].astype(str).str.replace(',', '', regex=False).str.extract(r'(\d+\.?\d*)', expand=False).astype(float).fillna(0)
            return pd.Series(0, index=df.index)

        # Tự động dò tìm các cột (dù bạn đổi tên cột cũng không sao)
        col_model = find_col(['Model Name', 'Model', 'name', 'Tên'])
        col_ram = find_col(['RAM', 'ram', 'Ram', 'RAM/Front Camera'])
        col_front_cam = find_col(['Front Camera', 'front_camera', 'Selfie'])
        col_back_cam = find_col(['Back Camera', 'back_camera', 'Main Camera'])
        col_screen = find_col(['Screen Size', 'screen', 'Display'])
        col_weight = find_col(['Mobile Weight', 'weight', 'Weight'])
        col_battery = find_col(['Battery Capacity', 'battery', 'Pin'])
        col_price = find_col(['Launched Price (USA)', 'Price (India)', 'price', 'Price', 'Price_USD'])
        col_proc = find_col(['Processor', 'processor', 'Chip'])

        # Trích xuất dữ liệu an toàn
        if col_model:
            df = df.dropna(subset=[col_model])
            df = df[df[col_model].astype(str).str.strip() != '']
            
            if len(df) > 0:
                df['Model Name'] = df[col_model]
                df['RAM_val'] = safe_extract(col_ram)
                df['Front_MP'] = safe_extract(col_front_cam)
                df['Back_MP'] = safe_extract(col_back_cam)
                df['Screen_val'] = safe_extract(col_screen)
                df['Weight_val'] = safe_extract(col_weight)
                df['Battery_val'] = safe_extract(col_battery)
                
                df['Price_USD'] = safe_extract(col_price)
                df['Price_USD'] = df['Price_USD'].replace(0, 999) # Chống lỗi chia 0

                def proc_score(p):
                    match = re.search(r'A(\d+)', str(p))
                    return float(match.group(1)) if match else 10.0
                df['Proc_score'] = df[col_proc].apply(proc_score) if col_proc else 10.0
        else:
            df = pd.DataFrame()

        # Kiểm tra bước cuối
        if len(df) == 0:
            print("\n[!] CẢNH BÁO: Dữ liệu vẫn trống. Kích hoạt Demo 10 máy!\n")
            dummy_data = {
                'Model Name': ['iPhone 15 Pro Max', 'Samsung S24 Ultra', 'Xiaomi 14 Pro', 'Oppo Find X7 Ultra', 'Vivo X100 Pro', 'Google Pixel 8 Pro', 'OnePlus 12', 'Huawei P60 Pro', 'Sony Xperia 1 V', 'Asus ROG Phone 8'],
                'RAM_val': [8.0, 12.0, 16.0, 16.0, 16.0, 12.0, 16.0, 8.0, 12.0, 16.0],
                'Front_MP': [12.0, 12.0, 32.0, 32.0, 32.0, 10.5, 32.0, 13.0, 12.0, 32.0],
                'Back_MP': [48.0, 200.0, 50.0, 50.0, 50.0, 50.0, 50.0, 48.0, 48.0, 50.0],
                'Screen_val': [6.7, 6.8, 6.73, 6.82, 6.78, 6.7, 6.82, 6.67, 6.5, 6.78],
                'Weight_val': [221.0, 232.0, 223.0, 221.0, 221.0, 213.0, 220.0, 200.0, 187.0, 225.0],
                'Battery_val': [4422.0, 5000.0, 4880.0, 5000.0, 5400.0, 5050.0, 5400.0, 4815.0, 5000.0, 5500.0],
                'Price_USD': [1199.0, 1299.0, 899.0, 950.0, 900.0, 999.0, 799.0, 899.0, 1199.0, 1099.0],
                'Proc_score': [17.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
            }
            df = pd.DataFrame(dummy_data)
        else:
            print(f"\n[★] XUẤT SẮC! Đã nạp thành công {len(df)} dòng dữ liệu điện thoại thật!")
            print(f"[★] Máy test mẫu: {df.iloc[0]['Model Name']} | Giá: ${df.iloc[0]['Price_USD']} | Pin: {df.iloc[0]['Battery_val']} mAh\n")

        self.df = df

    def rank_phones(self, ai_weights):
        df = self.df.copy()
        if len(df) == 0: return []

        for col in ['RAM_val', 'Battery_val', 'Screen_val', 'Front_MP', 'Back_MP', 'Proc_score']:
            max_val, min_val = df[col].max(), df[col].min()
            df[f'Norm_{col}'] = (df[col] - min_val) / (max_val - min_val) if max_val > min_val else 0.5

        for col in ['Price_USD', 'Weight_val']:
            max_val, min_val = df[col].max(), df[col].min()
            df[f'Norm_{col}'] = (max_val - df[col]) / (max_val - min_val) if max_val > min_val else 0.5

        df['Score_Gia'] = df['Norm_Price_USD']
        df['Score_HieuNang'] = (df['Norm_RAM_val'] * 0.5) + (df['Norm_Proc_score'] * 0.5)
        df['Score_TraiNghiem'] = (df['Norm_Battery_val'] * 0.4) + (df['Norm_Screen_val'] * 0.3) + (df['Norm_Weight_val'] * 0.3)
        df['Score_Camera'] = (df['Norm_Back_MP'] * 0.7) + (df['Norm_Front_MP'] * 0.3)

        df['Total_score'] = (
            df['Score_Gia'] * ai_weights['Giá'] +
            df['Score_HieuNang'] * ai_weights['Hiệu năng'] +
            df['Score_TraiNghiem'] * ai_weights['Trải nghiệm'] +
            df['Score_Camera'] * ai_weights['Camera']
        )

        top_phones = df.sort_values(by='Total_score', ascending=False).head(10)
        
        result = []
        for _, row in top_phones.iterrows():
            result.append({
                'Model Name': row['Model Name'],
                'Total_score': round(row['Total_score'], 4),
                'Price': row['Price_USD'],
                'Battery': row['Battery_val'],
                'Camera': f"{row['Back_MP']}MP / {row['Front_MP']}MP"
            })
        return result
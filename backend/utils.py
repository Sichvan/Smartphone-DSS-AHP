# Normalize functions (min-max, tùy criteria: high good or low good)
def normalize_value(value, crit):
    # Hardcode min-max tạm thời dựa trên dataset iPhone của bạn
    # Sau này nên query min/max từ DB cho dynamic
    if crit == 'battery':
        min_val, max_val = 3200, 4500  # Từ dataset
        return (value - min_val) / (max_val - min_val) if max_val > min_val else 0.5
    elif crit == 'screen':
        min_val, max_val = 6.1, 6.7
        return (value - min_val) / (max_val - min_val)
    elif crit == 'ram':  # RAM là string như '6GB', parse số
        try:
            val = float(value.replace('GB', '').strip())
            return val / 12.0  # Giả sử max 12GB
        except:
            return 0.5
    elif crit == 'price':
        min_val, max_val = 50000, 350000  # INR hoặc PKR, adjust theo cột bạn dùng (price_india)
        return (max_val - value) / (max_val - min_val)  # Giá thấp tốt hơn
    elif crit == 'weight':
        min_val, max_val = 170, 230  # g
        return (max_val - value) / (max_val - min_val)  # Nhẹ tốt hơn
    # Thêm cho camera (parse MP), processor (khó hơn, tạm 0.5)
    return 0.5  # Default

def generate_explanation(ranked):
    """Tạo explanation XAI"""
    exp = "Xếp hạng dựa trên AHP:\n"
    for model, score, details in ranked:
        exp += f"- {model}: Score {score:.2f}. Lý do: Pin {details['battery_capacity']}mAh, Giá {details['price_india']} INR.\n"
    return exp
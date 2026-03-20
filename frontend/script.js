// ==========================================
// 1. Hàm điền gợi ý nhanh vào ô nhập liệu
// ==========================================
function fillSuggestion(btn) {
    document.getElementById('userInput').value = btn.innerText;
}

// ==========================================
// 2. Tính năng bật/tắt thanh Sidebar Lịch Sử
// ==========================================
async function toggleHistory() {
    const sidebar = document.getElementById('history-sidebar');
    const overlay = document.getElementById('history-overlay');
    
    // Đóng Sidebar nếu đang mở
    if (sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
        return;
    }
    
    // Mở Sidebar và kéo dữ liệu từ API
    try {
        const res = await fetch('/history');
        const data = await res.json();
        
        if (data.status === 'success') {
            let html = '';
            // Giao diện khi chưa có lịch sử
            if (data.history.length === 0) {
                html = `
                <div style="text-align:center; padding: 40px 0;">
                    <i class="fa-solid fa-box-open" style="font-size: 48px; color: #cbd5e1; margin-bottom: 16px;"></i>
                    <p style="color: #64748b; font-size: 14px; font-weight: 500;">Chưa có dữ liệu lịch sử.<br>Hãy tìm kiếm để hệ thống ghi nhận!</p>
                </div>`;
            } else {
                // Đổ dữ liệu lịch sử
                data.history.forEach(item => {
                    let phonesHtml = '';
                    item.top_phones.forEach((p, idx) => {
                        let rankColor = idx === 0 ? '#f59e0b' : '#94a3b8'; 
                        phonesHtml += `
                        <div class="hist-phone-chip">
                            <span><i class="fa-solid fa-medal" style="color: ${rankColor}; margin-right: 6px;"></i> ${p['Model Name']}</span>
                            <span style="color: #ef4444; font-weight: 700;">$${p['Price']}</span>
                        </div>`;
                    });

                    html += `
                    <div class="hist-item">
                        <div class="hist-time"><i class="fa-regular fa-clock"></i> ${item.created_at}</div>
                        <div class="hist-query">"${item.user_text}"</div>
                        <div class="hist-phones">${phonesHtml}</div>
                    </div>`;
                });
            }
            document.getElementById('history-container').innerHTML = html;
            
            // Kích hoạt animation trượt ra
            sidebar.classList.add('active');
            overlay.classList.add('active');
        }
    } catch (error) {
        alert("Chưa lấy được lịch sử. Vui lòng kiểm tra lại kết nối Database PostgreSQL!");
        console.error(error);
    }
}

// ==========================================
// 3. Xử lý Gửi yêu cầu phân tích AHP
// ==========================================
async function analyzeDemand() {
    const text = document.getElementById('userInput').value;
    if (!text.trim()) {
        alert("Vui lòng nhập nhu cầu của bạn!"); return;
    }

    // Reset UI và bật Loading
    document.getElementById('candidates-section').style.display = 'none';
    document.getElementById('matrix-section').style.display = 'none';
    document.getElementById('ranking-section').style.display = 'none';
    document.getElementById('loading-spinner').style.display = 'block';

    try {
        const res = await fetch('/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: text })
        });
        const data = await res.json();
        
        document.getElementById('loading-spinner').style.display = 'none';

        if (data.status === 'success') {
            // ------------------------------------------
            // BƯỚC 1: Render 10 Phương án đề xuất
            // ------------------------------------------
            let candHtml = '';
            data.candidates.forEach(phone => {
                candHtml += `
                <div class="candidate-item">
                    <div style="width: 40px; height: 40px; border-radius: 10px; background: #e0e7ff; color: #4f46e5; display: flex; justify-content: center; align-items: center; font-size: 18px;">
                        <i class="fa-solid fa-mobile-screen"></i>
                    </div>
                    <div>
                        <div style="font-weight: 600; font-size: 15px; color: #0f172a;">${phone['Model Name']}</div>
                        <div style="font-size: 13px; color: #64748b; margin-top: 2px;">$${phone['Price']} &bull; Pin: ${phone['Battery']}</div>
                    </div>
                </div>`;
            });
            document.getElementById('candidates-container').innerHTML = candHtml;
            document.getElementById('candidates-section').style.display = 'block';

            // ------------------------------------------
            // BƯỚC 2: Render Ma trận AHP
            // ------------------------------------------
            const criteria = ["Giá", "Hiệu năng", "Trải nghiệm", "Camera"];
            let matrixHtml = `<thead><tr><th>Tiêu chí</th>`;
            criteria.forEach(c => matrixHtml += `<th>${c}</th>`);
            matrixHtml += `</tr></thead><tbody>`;
            
            for(let r = 0; r < 4; r++) {
                matrixHtml += `<tr><th>${criteria[r]}</th>`;
                for(let c = 0; c < 4; c++) {
                    let val = data.matrix[r][c].toFixed(2);
                    let classDiag = (r === c) ? 'class="diagonal"' : '';
                    matrixHtml += `<td ${classDiag}>${val}</td>`;
                }
                matrixHtml += `</tr>`;
            }
            matrixHtml += `</tbody>`;
            document.getElementById('matrix-table').innerHTML = matrixHtml;
            
            document.getElementById('matrix-explanation').innerHTML = `
                <div style="background: #f0fdf4; color: #065f46; padding: 14px 18px; border-radius: 12px; border: 1px solid #a7f3d0; font-size: 14px; font-weight: 500;">
                    <i class="fa-solid fa-robot" style="margin-right: 8px;"></i> ${data.explanation}
                </div>`;
            document.getElementById('matrix-section').style.display = 'block';

            // ------------------------------------------
            // BƯỚC 3: Render Bảng Xếp Hạng Top 5
            // ------------------------------------------
            let rankHtml = '';
            data.ranking.forEach((phone, index) => {
                let rankClass = 'rank-other';
                if(index === 0) rankClass = 'rank-1';
                else if(index === 1) rankClass = 'rank-2';
                else if(index === 2) rankClass = 'rank-3';

                rankHtml += `
                <div class="rank-item">
                    <div style="display: flex; gap: 18px; align-items: center;">
                        <div class="rank-badge ${rankClass}">
                            ${index === 0 ? '<i class="fa-solid fa-crown"></i>' : index + 1}
                        </div>
                        <div>
                            <h3 style="margin: 0; font-size: 17px; color: #0f172a; font-weight: 600;">${phone['Model Name']}</h3>
                            <div style="font-size: 13px; color: #64748b; margin-top: 8px; display: flex; gap: 12px;">
                                <span style="background: #f1f5f9; padding: 5px 10px; border-radius: 8px;"><i class="fa-solid fa-battery-full" style="color:#10b981;"></i> ${phone['Battery']} mAh</span>
                                <span style="background: #f1f5f9; padding: 5px 10px; border-radius: 8px;"><i class="fa-solid fa-camera" style="color:#3b82f6;"></i> ${phone['Camera']}</span>
                            </div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-weight: 800; font-size: 20px; color: #ef4444;">$${phone['Price']}</div>
                        <div style="font-size: 13px; color: #10b981; font-weight: 700; margin-top: 6px;">Điểm AHP: ${phone['Total_score']}</div>
                    </div>
                </div>`;
            });
            document.getElementById('ranking-container').innerHTML = rankHtml;
            document.getElementById('ranking-section').style.display = 'block';
        }
    } catch (error) {
        document.getElementById('loading-spinner').innerHTML = '<p style="color: #ef4444; font-weight:600;"><i class="fa-solid fa-triangle-exclamation"></i> Lỗi kết nối với Backend!</p>';
    }
}
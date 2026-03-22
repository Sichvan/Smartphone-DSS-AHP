// ==========================================
// 1. CÁC HÀM TIỆN ÍCH UI
// ==========================================

function fillSuggestion(element) {
    document.getElementById('userInput').value = element.innerText;
}

function toggleHistory() {
    const sidebar = document.getElementById('history-sidebar');
    const overlay = document.getElementById('history-overlay');
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
    
    if (sidebar.classList.contains('active')) {
        loadHistory();
    }
}

// ==========================================
// 2. HÀM CHÍNH: PHÂN TÍCH NHU CẦU
// ==========================================

async function analyzeDemand() {
    const userInput = document.getElementById('userInput').value;
    if (!userInput) {
        alert("Vui lòng nhập nhu cầu của bạn!");
        return;
    }

    // Hiển thị Loading và ẩn các kết quả cũ
    document.getElementById('loading-spinner').style.display = 'block';
    document.getElementById('candidates-section').style.display = 'none';
    document.getElementById('matrix-section').style.display = 'none';
    document.getElementById('ranking-section').style.display = 'none';

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: userInput })
        });

        const data = await response.json();

        if (data.status === 'success') {
            // --- BƯỚC 1: HIỂN THỊ 5 ỨNG VIÊN TIỀM NĂNG ---
            renderInitialCandidates(data.initial_candidates);
            document.getElementById('candidates-section').style.display = 'block';

            // --- BƯỚC 2: HIỂN THỊ CHI TIẾT CÁC BƯỚC TÍNH TOÁN AHP ---
            renderAHPSteps(data.ahp_steps);
            document.getElementById('matrix-section').style.display = 'block';

            // --- BƯỚC 3: HIỂN THỊ KẾT QUẢ XẾP HẠNG CUỐI CÙNG ---
            renderFinalRanking(data.final_ranking);
            document.getElementById('ranking-section').style.display = 'block';

            // Cuộn mượt xuống phần kết quả
            document.getElementById('candidates-section').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert("Lỗi: " + data.message);
        }
    } catch (error) {
        console.error("Error:", error);
        alert("Không thể kết nối với Server!");
    } finally {
        document.getElementById('loading-spinner').style.display = 'none';
    }
}

// ==========================================
// 3. CÁC HÀM HIỂN THỊ DỮ LIỆU (RENDER)
// ==========================================

// BƯỚC 1: Render danh sách 5 ứng viên ban đầu
function renderInitialCandidates(candidates) {
    const container = document.getElementById('candidates-container');
    container.innerHTML = ''; 

    candidates.forEach(p => {
        const chip = document.createElement('div');
        chip.className = 'candidate-chip';
        chip.style = "background: #fff; padding: 12px 20px; border-radius: 10px; border: 1px solid #e5e7eb; display: flex; align-items: center; gap: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); font-weight: 600; color: #374151;";
        chip.innerHTML = `<i class="fa-solid fa-mobile-screen-button" style="color: #4f46e5;"></i> ${p['Model Name']}`;
        container.appendChild(chip);
    });
}

// BƯỚC 2: Render các Ma trận so sánh cặp, Trọng số và Giải thích
function renderAHPSteps(steps) {
    const container = document.getElementById('matrix-table'); // Đây là thẻ <table> trong HTML, nhưng ta sẽ dùng nó làm container chứa các div
    container.innerHTML = ''; 

    steps.forEach((step, index) => {
        const stepDiv = document.createElement('div');
        stepDiv.className = 'ahp-step-card';
        stepDiv.style = "margin-bottom: 40px; border-bottom: 2px dashed #f3f4f6; padding-bottom: 20px;";

        let html = `
            <h3 style="color: #4338ca; margin-bottom: 10px;">${index + 1}. ${step.step_name}</h3>
            <p style="color: #6b7280; font-style: italic; margin-bottom: 15px; background: #f9fafb; padding: 10px; border-radius: 8px;">
                <i class="fa-solid fa-comment-dots"></i> ${step.explanation}
            </p>
            <div class="table-responsive">
                <table class="ahp-table" style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f3f4f6;">
                            <th style="padding: 10px; border: 1px solid #e5e7eb;">Đối tượng</th>
                            ${step.labels.map(l => `<th style="padding: 10px; border: 1px solid #e5e7eb;">${l}</th>`).join('')}
                            <th style="padding: 10px; border: 1px solid #e5e7eb; background: #e0e7ff; color: #4338ca;">Trọng số</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        step.matrix.forEach((row, i) => {
            html += `<tr>
                <td style="padding: 10px; border: 1px solid #e5e7eb; font-weight: bold; background: #f9fafb;">${step.labels[i]}</td>`;
            row.forEach(val => {
                html += `<td style="padding: 10px; border: 1px solid #e5e7eb; text-align: center;">${val.toFixed(2)}</td>`;
            });
            // Cột trọng số (nhân 100 để hiện %)
            html += `<td style="padding: 10px; border: 1px solid #e5e7eb; text-align: center; font-weight: bold; color: #4338ca; background: #f5f7ff;">
                        ${(step.weights[i] * 100).toFixed(1)}%
                    </td></tr>`;
        });

        const crColor = step.cr < 0.1 ? '#10b981' : '#ef4444';
        html += `
                    </tbody>
                </table>
            </div>
            <p style="margin-top: 10px; font-size: 0.9em; font-weight: 500;">
                Chỉ số nhất quán CR: <span style="color: ${crColor}">${step.cr.toFixed(4)}</span> 
                ${step.cr < 0.1 ? ' (✅ Hợp lệ)' : ' (⚠️ Cần xem xét)'}
            </p>
        `;
        stepDiv.innerHTML = html;
        container.appendChild(stepDiv);
    });
}

// BƯỚC 3: Render Xếp hạng cuối cùng
// BƯỚC 3: Render Xếp hạng cuối cùng
function renderFinalRanking(ranking) {
    const container = document.getElementById('ranking-container');
    container.innerHTML = '';

    ranking.forEach((item, index) => {
        const card = document.createElement('div');
        card.className = `rank-item`; 
        
        let badgeClass = 'rank-other';
        if (index === 0) badgeClass = 'rank-1';
        else if (index === 1) badgeClass = 'rank-2';
        else if (index === 2) badgeClass = 'rank-3';

        // TÍNH TOÁN VÀ ĐỊNH DẠNG TIỀN VIỆT
        // Nhân với 26000 và thêm dấu chấm phân cách hàng nghìn
        const priceVND = (item.Price_USD * 26000).toLocaleString('vi-VN');

        card.innerHTML = `
            <div class="rank-badge ${badgeClass}">${index + 1}</div>
            <div class="phone-info" style="flex: 1; margin-left: 15px;">
                <h3 style="margin: 0 0 8px 0; color: #0f172a; font-size: 18px;">${item['Model Name']}</h3>
                <div class="phone-specs" style="display: flex; gap: 15px; font-size: 13px; color: #64748b;">
                    <span><i class="fa-solid fa-microchip"></i> RAM: ${item.RAM_val}GB</span>
                    <span><i class="fa-solid fa-battery-full"></i> Pin: ${item.Battery_val}mAh</span>
                    <span style="font-weight: 600; color: #10b981;"><i class="fa-solid fa-tag"></i> ${priceVND} VNĐ</span>
                </div>
            </div>
            <div class="score-tag" style="text-align: right; background: #f8fafc; padding: 10px 15px; border-radius: 12px; border: 1px solid #e2e8f0;">
                <small style="display: block; font-size: 11px; color: #64748b; text-transform: uppercase; margin-bottom: 4px; font-weight: 600;">Điểm AHP</small>
                <strong style="color: #4338ca; font-size: 18px;">${item.final_ahp_score}</strong>
            </div>
        `;
        container.appendChild(card);
    });
}

// ==========================================
// 4. LỊCH SỬ (HISTORY)
// ==========================================

async function loadHistory() {
    const container = document.getElementById('history-container');
    
    // 1. Cải thiện UI lúc đang chờ tải dữ liệu
    container.innerHTML = `
        <div style="text-align: center; padding: 40px 0;">
            <div class="spinner"></div>
            <p style="color: #64748b; margin-top: 15px; font-size: 14px; font-weight: 500;">Đang nạp lịch sử...</p>
        </div>`;
    
    try {
        const res = await fetch('/history');
        const data = await res.json();
        
        if (data.history && data.history.length > 0) {
            container.innerHTML = data.history.map(h => {
                // 2. Xử lý chuỗi JSON từ database trả về dạng mảng
                let phonesData = [];
                try {
                    phonesData = typeof h.top_phones === 'string' ? JSON.parse(h.top_phones) : h.top_phones;
                } catch(e) { console.error("Lỗi phân giải JSON:", e); }

                // 3. Render danh sách các thẻ (chip) điện thoại
                let phonesHtml = '';
                if (Array.isArray(phonesData)) {
                    phonesHtml = phonesData.map((p, index) => `
                        <div class="hist-phone-chip">
                            <span><strong style="color: #3b82f6;">#${index + 1}</strong> ${p['Model Name']}</span>
                            <span style="background: #e0e7ff; color: #4338ca; padding: 2px 6px; border-radius: 6px; font-size: 11px; font-weight: 700;">
                                $${p['Price_USD']}
                            </span>
                        </div>
                    `).join('');
                }

                // 4. Khớp chính xác tên biến từ DB: user_text, created_at
                // Kết hợp sử dụng các class CSS có sẵn của bạn để giao diện đẹp hơn
                return `
                    <div class="hist-item">
                        <div class="hist-time">
                            <i class="fa-regular fa-clock"></i> ${h.created_at}
                        </div>
                        <div class="hist-query">
                            <i class="fa-solid fa-quote-left" style="color: #cbd5e1; margin-right: 6px; font-size: 12px;"></i>
                            ${h.user_text}
                        </div>
                        <div class="hist-phones">
                            ${phonesHtml}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            // UI Khi lịch sử trống
            container.innerHTML = `
                <div style="text-align: center; padding: 60px 20px; color: #94a3b8;">
                    <i class="fa-solid fa-clock-rotate-left" style="font-size: 40px; margin-bottom: 15px; opacity: 0.5;"></i>
                    <p style="font-size: 14px; font-weight: 500;">Bạn chưa có lịch sử tìm kiếm nào.</p>
                </div>`;
        }
    } catch (e) {
        // UI Khi lỗi kết nối Database
        container.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: #ef4444;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 35px; margin-bottom: 15px; opacity: 0.8;"></i>
                <p style="font-size: 14px; font-weight: 500;">Lỗi kết nối cơ sở dữ liệu.</p>
            </div>`;
    }
}

async function clearHistory() {
    if (!confirm("Bạn có chắc chắn muốn xóa toàn bộ lịch sử không?")) {
        return;
    }
    
    try {
        const response = await fetch('/history', { method: 'DELETE' });
        const data = await response.json();
        
        if (data.status === 'success') {
            loadHistory(); // Cập nhật lại UI ngay lập tức
        } else {
            alert("Lỗi khi xóa: " + data.message);
        }
    } catch (error) {
        alert("Không thể kết nối với máy chủ!");
    }
}
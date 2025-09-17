document.addEventListener('DOMContentLoaded', () => {
    console.log('downpanel.js: DOMContentLoaded event fired.');
    const singleDateInput = document.getElementById('downpanel_single_date_input');

    // =================================================
    // Element Selectors
    // =================================================
    const downPanel = document.getElementById('down-panel');
    const openBtn = document.getElementById('open-down-panel-btn');
    const closeBtn = document.getElementById('close-down-panel-btn');
    const table = document.querySelector('.excel-table');
    const addRowBtn = document.getElementById("add-row-btn");
    const resetBtn = document.getElementById("reset-btn");
    const saveBtn = document.getElementById('save-bulk-btn');

    if (!table) return;
    const tbody = table.querySelector('tbody');

    // =================================================
    // Variables & Helpers
    // =================================================
    let activeCell = { row: 0, col: 0 };
    let isFilling = false;
    let startFillCell = null;
    let endFillCell = null;
    const fillHandle = document.createElement('div');
    fillHandle.className = 'fill-handle';

    const getCell = (row, col) => tbody.rows[row]?.cells[col + 1];
    const getInput = (row, col) => getCell(row, col)?.querySelector('input, select');

    // =================================================
    // Categories
    // =================================================
    const incomeCategories = ["월급", "보너스", "이자소득", "기타수입", "부수입", "용돈", "상여", "금융소득"];
    const expenseCategories = [
        "식비", "교통/차량", "문화생활", "마트/편의점", "패션/미용",
        "생활용품", "주거/통신", "건강", "교육", "경조사/회비", "부모님", "기타"
    ];

    // =================================================
    // Panel Open/Close
    // =================================================
    if (openBtn) openBtn.addEventListener('click', () => downPanel?.classList.add('open'));
    if (closeBtn) closeBtn.addEventListener('click', () => downPanel?.classList.remove('open'));

    // =================================================
    // Single Date Input (상단 단일 입력)
    // =================================================
    if (singleDateInput) {
        const today = new Date();
        const formattedDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        singleDateInput.value = formattedDate;
    }

    // =================================================
    // Utility Functions
    // =================================================
    const formatDateInput = (e) => {
        let input = e.target;
        let value = input.value.replace(/[^0-9]/g, '');
        if (value.length > 4) value = value.substring(0, 4) + '-' + value.substring(4);
        if (value.length > 7) value = value.substring(0, 7) + '-' + value.substring(7, 9);
        input.value = value;
    };

    const formatNumber = (value) => {
        if (!value) return "";
        const num = value.toString().replace(/[^0-9]/g, "");
        return num.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    };

    // =================================================
    // Row Binding
    // =================================================
    const bindRowEvents = (row) => {
        console.log('downpanel.js: Binding events for new row.', row);

        // 수입/지출 색상 + 카테고리
        const typeSelect = row.querySelector('.type-select');
        if (typeSelect) {
            typeSelect.addEventListener('change', () => {
                const categorySelect = row.querySelector(".category-select");
                let categories = [];
                if (typeSelect.value === "수입") {
                    typeSelect.style.color = "blue";
                    categories = incomeCategories;
                } else if (typeSelect.value === "지출") {
                    typeSelect.style.color = "red";
                    categories = expenseCategories;
                } else {
                    typeSelect.style.color = "black";
                }

                if (categorySelect) {
                    categorySelect.innerHTML = '<option value="">--분류--</option>';
                    categories.forEach(cat => {
                        const opt = document.createElement("option");
                        opt.value = cat;
                        opt.textContent = cat;
                        categorySelect.appendChild(opt);
                    });
                }
            });
        }

        // 금액 입력: 숫자만 허용 + blur 시 콤마
        const amountInput = row.querySelector('td:nth-child(6) input');
        if (amountInput) {
            amountInput.addEventListener("input", () => {
                amountInput.value = amountInput.value.replace(/[^0-9]/g, "");
            });
            amountInput.addEventListener("blur", () => {
                amountInput.value = formatNumber(amountInput.value);
            });
        }

        // 날짜 입력
        const rowDateInput = row.querySelector('.bulk-date-input');
        if (rowDateInput) {
            rowDateInput.addEventListener('input', formatDateInput);
        }
    };

    // 초기 행 바인딩
    tbody.querySelectorAll('tr').forEach(row => bindRowEvents(row));
    updateRowNumbers();

    // =================================================
    // Drag Fill Logic
    // =================================================
    tbody.addEventListener('mousedown', (e) => {
        const cell = e.target.closest('td');
        if (!cell) return;

        if (e.target.closest('.delete-row')) return;

        if (e.target === fillHandle) {
            isFilling = true;
            startFillCell = { row: cell.parentElement.rowIndex - 1, col: cell.cellIndex - 1 };
            e.preventDefault();
            return;
        }

        const input = cell.querySelector('input, select, .bulk-date-input');
        if (input) input.focus();

        tbody.querySelectorAll('.active').forEach(c => c.classList.remove('active'));
        cell.classList.add('active');
        activeCell = { row: cell.parentElement.rowIndex - 1, col: cell.cellIndex - 1 };
        cell.appendChild(fillHandle);
    });

    tbody.addEventListener('mousemove', (e) => {
        if (!isFilling) return;
        const cell = e.target.closest('td');
        if (!cell) return;

        const rowIndex = cell.parentElement.rowIndex - 1;
        const colIndex = cell.cellIndex - 1;
        if (colIndex !== startFillCell.col) return;

        endFillCell = { row: rowIndex, col: colIndex };
        tbody.querySelectorAll('.filling').forEach(c => c.classList.remove('filling'));
        const minRow = Math.min(startFillCell.row, endFillCell.row);
        const maxRow = Math.max(startFillCell.row, endFillCell.row);
        for (let i = minRow; i <= maxRow; i++) {
            getCell(i, startFillCell.col)?.classList.add('filling');
        }
    });

    window.addEventListener('mouseup', () => {
        if (isFilling && startFillCell && endFillCell) {
            const startInput = getCell(startFillCell.row, startFillCell.col)?.querySelector('input, select');
            if (startInput) {
                const startValue = startInput.value;
                const minRow = Math.min(startFillCell.row, endFillCell.row);
                const maxRow = Math.max(startFillCell.row, endFillCell.row);
                for (let i = minRow; i <= maxRow; i++) {
                    const targetInput = getCell(i, startFillCell.col)?.querySelector('input, select');
                    if (targetInput) targetInput.value = startValue;
                }
            }
        }
        isFilling = false;
        startFillCell = null;
        endFillCell = null;
        tbody.querySelectorAll('.filling').forEach(c => c.classList.remove('filling'));
    });

    // =================================================
    // Panel Footer Buttons
    // =================================================
    const baseRowHTML = `
      <th></th>
      <td>
        <select class="type-select">
          <option value="">--선택--</option>
          <option value="수입">수입</option>
          <option value="지출">지출</option>
        </select>
      </td>
      <td class="date-cell">
        <input type="text" class="bulk-date-input" placeholder="YYYY-MM-DD">
      </td>
      <td>
        <select>
          <option value="">--선택--</option>
          <option value="현금">현금</option>
          <option value="은행">은행</option>
          <option value="카드">카드</option>
        </select>
      </td>
      <td>
        <select class="category-select">
          <option value="">--분류--</option>
        </select>
      </td>
      <td><input type="text"></td>
      <td><input type="text"></td>
      <td><input type="text"></td>
      <td><button class="delete-row">×</button></td>
    `;

    function updateRowNumbers() {
        tbody.querySelectorAll('tr').forEach((row, i) => {
            const th = row.querySelector("th");
            if (th) th.textContent = i + 1;
        });
    }

    function createNewRow() {
        const newRow = tbody.insertRow();
        newRow.innerHTML = baseRowHTML;
        bindRowEvents(newRow);
        updateRowNumbers();
        return newRow;
    }

    if (addRowBtn) addRowBtn.addEventListener("click", () => createNewRow());
    if (resetBtn) resetBtn.addEventListener("click", () => {
        tbody.innerHTML = "";
        for (let i = 0; i < 10; i++) createNewRow();
    });

    // =================================================
    // Save Bulk Transactions
    // =================================================
    if (saveBtn) {
        saveBtn.addEventListener('click', () => {
            const tableRows = tbody.querySelectorAll('tr');
            const transactions = [];
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
            let hasError = false;

            for (const row of tableRows) {
                const type = row.cells[1].querySelector('select')?.value || '';
                const date = row.cells[2].querySelector('input')?.value.trim() || '';
                const asset = row.cells[3].querySelector('select')?.value || '';
                const category = row.cells[4].querySelector('select')?.value || '';
                const amount = row.cells[5].querySelector('input')?.value.replace(/,/g, '') || '';
                const content = row.cells[6].querySelector('input')?.value || '';
                const memo = row.cells[7].querySelector('input')?.value || '';

                if (type || amount) {
                    if (!type || !amount || !date || !dateRegex.test(date)) {
                        alert('날짜, 구분, 금액을 확인해주세요 (YYYY-MM-DD 형식).');
                        row.cells[2].querySelector('input')?.focus();
                        hasError = true;
                        break;
                    }

                    transactions.push({ type, date, asset, category, amount, content, memo });
                }
            }

            if (hasError || transactions.length === 0) {
                if (!hasError) alert('저장할 내역이 없습니다.');
                return;
            }

            fetch('/accbook/save_bulk_transactions/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({ transactions }),
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert('저장되었습니다.');
                    window.location.reload();
                } else {
                    alert('저장 실패: ' + (data.error || '알 수 없는 오류'));
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('저장 중 오류 발생: ' + (err.message || err));
            });
        });
    }
});

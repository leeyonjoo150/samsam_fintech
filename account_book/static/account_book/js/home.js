document.addEventListener("DOMContentLoaded", () => {
    console.log("home.js: DOMContentLoaded event fired.");

    // =================================================
    // Excel Export
    // =================================================
    const excelBtn = document.querySelector(".excel-icon");
    if (excelBtn) {
        excelBtn.addEventListener("click", () => {
            const year = currentYear;   // Django 템플릿에서 정의됨
            const month = currentMonth;
            window.location.href = `/accbook/export/${year}/${month}/`;
        });
    }

    // =================================================
    // Alert Bar & Delete Selected Records
    // =================================================
    bindMasterCheckbox();

    const deleteBtn = document.querySelector(".alert-actions .material-icons.delete");
    if (deleteBtn) {
        deleteBtn.style.cursor = "pointer";
        deleteBtn.addEventListener("click", deleteSelectedRecords);
    }

    const closeBtn = document.querySelector(".alert-bar .alert-close-button");
    if (closeBtn) {
        closeBtn.style.cursor = "pointer";
        closeBtn.addEventListener("click", () => {
            clearAllSelections();
            updateAlertBar();
        });
    }

    // =================================================
    // Search Functionality (날짜 + 수입/지출)
    // =================================================
    const toggleSearchBtn = document.getElementById("toggle-search-btn");
    const dateNavigationArea = document.getElementById("date-navigation-area");
    const searchFormArea = document.getElementById("search-form-area");

    const searchStartDateInput = document.getElementById("search-start-date-input");
    const searchEndDateInput = document.getElementById("search-end-date-input");
    const searchExpenseBtn = document.getElementById("search-expense-btn");
    const searchIncomeBtn = document.getElementById("search-income-btn");
    const searchResetBtn = document.getElementById("search-reset-btn");
    const executeSearchBtn = document.getElementById("execute-search-btn");

    let selectedSearchType = null; 
    let currentYear = new Date().getFullYear();
    let currentMonth = new Date().getMonth() + 1;

    function toggleSearchForm() {
        if (dateNavigationArea.style.display !== "none") {
            dateNavigationArea.style.display = "none";
            searchFormArea.style.display = "flex";
        } else {
            dateNavigationArea.style.display = "flex";
            searchFormArea.style.display = "none";
        }
    }
    if (toggleSearchBtn) toggleSearchBtn.addEventListener("click", toggleSearchForm);

    // 수입/지출 필터 버튼
    if (searchExpenseBtn) {
        searchExpenseBtn.addEventListener("click", () => {
            searchExpenseBtn.classList.toggle("active");
            searchIncomeBtn.classList.remove("active");
            selectedSearchType = searchExpenseBtn.classList.contains("active") ? "expense" : null;
        });
    }
    if (searchIncomeBtn) {
        searchIncomeBtn.addEventListener("click", () => {
            searchIncomeBtn.classList.toggle("active");
            searchExpenseBtn.classList.remove("active");
            selectedSearchType = searchIncomeBtn.classList.contains("active") ? "income" : null;
        });
    }

    // 검색 실행
    if (executeSearchBtn) {
        executeSearchBtn.addEventListener("click", () => {
            const startDate = searchStartDateInput.value;
            const endDate = searchEndDateInput.value;
            performSearch(startDate, endDate, selectedSearchType);
        });
    }

    // 검색 리셋
    if (searchResetBtn) {
        searchResetBtn.addEventListener("click", () => {
            searchStartDateInput.value = "";
            searchEndDateInput.value = "";
            searchExpenseBtn.classList.remove("active");
            searchIncomeBtn.classList.remove("active");
            selectedSearchType = null;
            console.log("Search form reset. Loading default transactions.");
            loadDefaultTransactions();
        });
    }

// ✅ 거래 내역 테이블 렌더링 함수
function renderTransactions(transactions) {
    console.log("렌더링 시작:", transactions);
    const recordList = document.getElementById("record-list");
    recordList.innerHTML = "";

    if (!transactions || transactions.length === 0) {
        recordList.innerHTML = '<tr><td colspan="8" style="text-align: center;">데이터가 없습니다.</td></tr>';
        return;
    }

    transactions.forEach(transaction => {
        console.log("행 추가:", transaction);
        const row = document.createElement("tr");
        row.setAttribute("data-id", transaction.id);

        row.innerHTML = `
            <td><input type="checkbox" data-id="${transaction.id}"></td>
            <td>${transaction.use_date}</td>
            <td>${transaction.cash_side}</td>
            <td>${transaction.asset_type}</td>
            <td>${transaction.category_name || ""}</td>
            <td>${transaction.cash_amount ? transaction.cash_amount.toLocaleString() : 0}</td>
            <td>${transaction.cash_cont || ""}</td>
            <td>
                ${transaction.memo || ""}
                ${transaction.photo_url ? `<a href="${transaction.photo_url}" target="_blank">📷</a>` : ""}
            </td>
        `;

        recordList.appendChild(row);
    });

    // ✅ 새로 렌더링된 체크박스에 다시 바인딩
    bindMasterCheckbox();
}


// =================================================
// AJAX Search & Default Load
// =================================================

// ✅ 검색 실행 함수
async function performSearch(startDate, endDate, type) {
    const queryParams = new URLSearchParams();
    if (startDate) queryParams.append("start_date", startDate);
    if (endDate) queryParams.append("end_date", endDate);
    if (type) queryParams.append("type", type);

    try {
        const response = await fetch(`/accbook/search_transactions/?${queryParams.toString()}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        renderTransactions(data.transactions);
    } catch (error) {
        console.error("Error performing search:", error);
        alert("검색 중 오류가 발생했습니다.");
    }
}

   // ✅ 기본 로드 함수 (홈: 한 달치)
    async function loadDefaultTransactions() {
    try {
        const year = document.querySelector("#date-navigation-area").dataset.year;
        const month = document.querySelector("#date-navigation-area").dataset.month;

        // 👉 검색 API 재활용
        const response = await fetch(`/accbook/search_transactions/?year=${year}&month=${month}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        renderTransactions(data.transactions);
    } catch (error) {
        console.error("Error loading default transactions:", error);
        alert("거래 내역을 불러오는 중 오류가 발생했습니다.");
    }
}

    // ✅ 검색
    async function searchTransactions() {
        const queryParams = new URLSearchParams();

        const startDate = document.getElementById("search-start-date-input").value;
        const endDate = document.getElementById("search-end-date-input").value;

        if (startDate) queryParams.set("start_date", startDate);
        if (endDate) queryParams.set("end_date", endDate);

        const response = await fetch(`/accbook/search_transactions/?${queryParams.toString()}`);
        const data = await response.json();
        renderTransactions(data.transactions); // 👉 표만 교체
    }

    // ✅ 이벤트 바인딩
        loadDefaultTransactions();
        document.getElementById("execute-search-btn").addEventListener("click", searchTransactions);
    });

// =================================================
// Helper Functions
// =================================================
function updateAlertBar() {
    const checkedBoxes = document.querySelectorAll("tbody input[type='checkbox']:checked");
    const count = checkedBoxes.length;
    const alertBar = document.querySelector(".alert-bar");
    if (!alertBar) return;
    const alertText = alertBar.querySelector(".alert-bar-text span:last-child");

    if (count > 0) {
        if (alertText) alertText.textContent = `${count}개 내역이 선택되었습니다.`;
        alertBar.style.display = "flex";
    } else {
        alertBar.style.display = "none";
    }
}

function bindMasterCheckbox() {
    const headerCheckbox = document.querySelector("thead input[type='checkbox']");
    const rowCheckboxes = document.querySelectorAll("tbody input[type='checkbox']");
    if (!headerCheckbox) return;

    headerCheckbox.addEventListener("change", (e) => {
        rowCheckboxes.forEach(cb => cb.checked = e.target.checked);
        updateAlertBar();
    });

    rowCheckboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            const allChecked = Array.from(rowCheckboxes).every(cb => cb.checked);
            headerCheckbox.checked = allChecked;
            updateAlertBar();
        });
    });

    updateAlertBar();
}

function clearAllSelections() {
    const headerCheckbox = document.querySelector("thead input[type='checkbox']");
    const rowCheckboxes = document.querySelectorAll("tbody input[type='checkbox']");
    if (headerCheckbox) headerCheckbox.checked = false;
    rowCheckboxes.forEach(cb => cb.checked = false);
}

function deleteSelectedRecords() {
    const checkedBoxes = document.querySelectorAll("#record-list input[type='checkbox']:checked");
    if (checkedBoxes.length === 0) {
        alert("삭제할 항목을 선택하세요!");
        return;
    }
    if (!confirm(`선택한 ${checkedBoxes.length}개 항목을 삭제하시겠습니까?`)) return;

    const ids = Array.from(checkedBoxes).map(cb => cb.dataset.id);
    const csrfTokenInput = document.querySelector("input[name='csrfmiddlewaretoken']");
    if (!csrfTokenInput) {
        alert("CSRF 토큰을 찾을 수 없습니다. 다시 시도하세요.");
        return;
    }
    const csrfToken = csrfTokenInput.value;
    const deleteUrl = document.querySelector(".alert-actions .delete").dataset.deleteUrl;

    fetch(deleteUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ ids: ids }),
    })
    .then(response => {
        if (!response.ok) throw new Error("삭제 요청 실패");
        return response.json();
    })
    .then(data => {
        if (data.success) {
            ids.forEach(id => {
                const row = document.querySelector(`#record-list tr[data-id='${id}']`);
                if (row) row.remove();
            });
            alert("선택된 항목이 삭제되었습니다.");
            clearAllSelections();
        } else {
            alert("삭제 중 오류가 발생했습니다.");
        }
        updateAlertBar();
    })
    .catch(error => {
        console.error("Error:", error);
        alert("서버와 통신 중 문제가 발생했습니다.");
    });
}


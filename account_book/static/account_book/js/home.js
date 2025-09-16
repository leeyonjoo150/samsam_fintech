// home.js - 알림바 & 비동기 삭제 기능
document.addEventListener("DOMContentLoaded", () => {
    bindMasterCheckbox();

    // 삭제 버튼 이벤트 리스너
    const deleteBtn = document.querySelector(".alert-actions .material-icons.delete");
    if (deleteBtn) {
        deleteBtn.style.cursor = "pointer";
        deleteBtn.addEventListener("click", deleteSelectedRecords);
    }

    // 알림바 닫기 버튼
    const closeBtn = document.querySelector(".alert-bar .alert-close-button");
    if (closeBtn) {
        closeBtn.style.cursor = "pointer";
        closeBtn.addEventListener("click", () => {
            clearAllSelections();
            updateAlertBar();
        });
    }
});

// 🔔 알림바 상태 업데이트
function updateAlertBar() {
    const checkedBoxes = document.querySelectorAll("tbody input[type='checkbox']:checked");
    const count = checkedBoxes.length;
    const alertBar = document.querySelector(".alert-bar");

    if (!alertBar) return;

    const alertText = alertBar.querySelector(".alert-bar-text span:last-child");

    if (count > 0) {
        if (alertText) {
            alertText.textContent = `${count}개 내역이 선택되었습니다.`;
        }
        alertBar.style.display = "flex";
    } else {
        alertBar.style.display = "none";
    }
}

// ✅ 마스터 체크박스 기능
function bindMasterCheckbox() {
    const headerCheckbox = document.querySelector("thead input[type='checkbox']");
    const rowCheckboxes = document.querySelectorAll("tbody input[type='checkbox']");

    if (!headerCheckbox) return;

    // 헤더 체크박스 → 전체 선택/해제
    headerCheckbox.addEventListener("change", (e) => {
        rowCheckboxes.forEach(cb => cb.checked = e.target.checked);
        updateAlertBar();
    });

    // 각 행 체크박스 → 헤더 상태 갱신
    rowCheckboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            const allChecked = Array.from(rowCheckboxes).every(cb => cb.checked);
            headerCheckbox.checked = allChecked;
            updateAlertBar();
        });
    });

    // 페이지 로드 시 초기화
    updateAlertBar();
}

// ❌ 선택된 항목 삭제 (비동기)
function deleteSelectedRecords() {
    const checkedBoxes = document.querySelectorAll("#record-list input[type='checkbox']:checked");
    
    if (checkedBoxes.length === 0) {
        alert("삭제할 항목을 선택하세요!");
        return;
    }

    if (!confirm(`선택한 ${checkedBoxes.length}개 항목을 삭제하시겠습니까?`)) {
        return;
    }

    const ids = Array.from(checkedBoxes).map(cb => cb.dataset.id);

    // CSRF 토큰 가져오기
    const csrfTokenInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (!csrfTokenInput) {
        alert("CSRF 토큰을 찾을 수 없습니다. 다시 시도하세요.");
        return;
    }
    const csrfToken = csrfTokenInput.value;

    const deleteUrl = document.querySelector('.alert-actions .delete').dataset.deleteUrl;

    fetch(deleteUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ ids: ids }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("삭제 요청 실패");
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // 삭제된 ID 행 DOM에서 제거
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

// 🔄 체크박스 전체 해제
function clearAllSelections() {
    const headerCheckbox = document.querySelector("thead input[type='checkbox']");
    const rowCheckboxes = document.querySelectorAll("tbody input[type='checkbox']");
    if (headerCheckbox) headerCheckbox.checked = false;
    rowCheckboxes.forEach(cb => cb.checked = false);
}

// Search functionality
document.addEventListener("DOMContentLoaded", () => {
    const toggleSearchBtn = document.getElementById("toggle-search-btn");
    const dateNavigationArea = document.getElementById("date-navigation-area");
    const searchFormArea = document.getElementById("search-form-area");

    const searchStartDateInput = document.getElementById("search-start-date-input");
    const searchEndDateInput = document.getElementById("search-end-date-input");
    const searchExpenseBtn = document.getElementById("search-expense-btn");
    const searchIncomeBtn = document.getElementById("search-income-btn");
    const searchAmountInput = document.getElementById("search-amount-input");
    const searchResetBtn = document.getElementById("search-reset-btn");
    const executeSearchBtn = document.getElementById("execute-search-btn");

    const searchCategorySelect = document.getElementById("search-category-select");
    let selectedSearchType = null; // To store 'income' or 'expense'

    // Function to fetch categories from Django backend
    async function fetchCategories(type) {
        try {
            const response = await fetch(`/accbook/get_categories/?type=${type}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            return data.categories;
        } catch (error) {
            console.error("Error fetching categories:", error);
            return [];
        }
    }

    // Function to render categories in the dropdown
    function renderCategoryDropdown(categories) {
        searchCategorySelect.innerHTML = '<option value="">-- 카테고리 --</option>'; // Clear existing options
        categories.forEach(category => {
            const option = document.createElement("option");
            option.value = category.id; // Assuming category object has an 'id' and 'name'
            option.textContent = category.name;
            searchCategorySelect.appendChild(option);
        });
    }

    // Function to toggle visibility of date navigation and search form
    function toggleSearchForm() {
        if (dateNavigationArea.style.display !== "none") {
            dateNavigationArea.style.display = "none";
            searchFormArea.style.display = "flex"; // Use flex to maintain layout
        } else {
            dateNavigationArea.style.display = "flex";
            searchFormArea.style.display = "none";
        }
    }

    // Event listener for search icon
    if (toggleSearchBtn) {
        toggleSearchBtn.addEventListener("click", toggleSearchForm);
    }

    // No explicit click listeners for date inputs; native behavior should handle opening pickers.

    // Event listeners for filter buttons (지출, 수입)
    if (searchExpenseBtn) {
        searchExpenseBtn.addEventListener("click", async () => {
            searchExpenseBtn.classList.toggle("active");
            searchIncomeBtn.classList.remove("active");
            selectedSearchType = searchExpenseBtn.classList.contains("active") ? "expense" : null;

            if (selectedSearchType) {
                const categories = await fetchCategories(selectedSearchType);
                renderCategoryDropdown(categories);
                searchCategorySelect.style.display = 'block'; // Show dropdown
            } else {
                searchCategorySelect.style.display = 'none'; // Hide dropdown
                searchCategorySelect.value = ""; // Reset selected value
            }
        });
    }

    if (searchIncomeBtn) {
        searchIncomeBtn.addEventListener("click", async () => {
            searchIncomeBtn.classList.toggle("active");
            searchExpenseBtn.classList.remove("active");
            selectedSearchType = searchIncomeBtn.classList.contains("active") ? "income" : null;

            if (selectedSearchType) {
                const categories = await fetchCategories(selectedSearchType);
                renderCategoryDropdown(categories);
                searchCategorySelect.style.display = 'block'; // Show dropdown
            } else {
                searchCategorySelect.style.display = 'none'; // Hide dropdown
                searchCategorySelect.value = ""; // Reset selected value
            }
        });
    }

    // Event listener for Reset button
    if (searchResetBtn) {
        searchResetBtn.addEventListener("click", () => {
            searchStartDateInput.value = "";
            searchEndDateInput.value = "";
            searchAmountInput.value = "";
            searchExpenseBtn.classList.remove("active");
            searchIncomeBtn.classList.remove("active");
            selectedSearchType = null;
            searchCategorySelect.style.display = 'none'; // Hide dropdown
            searchCategorySelect.value = ""; // Reset selected value
            console.log("Search form reset.");
            // Optionally, hide search results and show all transactions
        });
    }

    // Event listener for Execute Search button
    if (executeSearchBtn) {
        executeSearchBtn.addEventListener("click", () => {
            const startDate = searchStartDateInput.value;
            const endDate = searchEndDateInput.value;
            const amount = searchAmountInput.value;

            performSearch(startDate, endDate, selectedSearchType, searchCategorySelect.value, amount);
        });
    }

    // Function to perform the search
    async function performSearch(startDate, endDate, type, categoryId, amount) {
        const queryParams = new URLSearchParams();
        if (startDate) queryParams.append('start_date', startDate);
        if (endDate) queryParams.append('end_date', endDate);
        if (type) queryParams.append('type', type);
        if (categoryId) queryParams.append('category', categoryId);
        if (amount) queryParams.append('amount', amount);

        try {
            const response = await fetch(`/accbook/search_transactions/?${queryParams.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            renderTransactions(data.transactions);
            updateSearchResultsDisplay(data.transactions.length, startDate, endDate);
            searchFormArea.style.display = "none"; // Hide search form after execution
            dateNavigationArea.style.display = "flex"; // Show date navigation area
        } catch (error) {
            console.error("Error performing search:", error);
            alert("검색 중 오류가 발생했습니다.");
        }
    }

    // Function to render transactions in the table
    function renderTransactions(transactions) {
        const recordList = document.getElementById("record-list");
        recordList.innerHTML = ''; // Clear existing transactions

        if (transactions.length === 0) {
            recordList.innerHTML = '<tr><td colspan="8" style="text-align: center;">검색 결과가 없습니다.</td></tr>';
            return;
        }

        transactions.forEach(transaction => {
            const row = document.createElement("tr");
            row.innerHTML = `
                <td><input type="checkbox" data-id="${transaction.id}"></td>
                <td>${transaction.use_date}</td>
                <td>${transaction.cash_side}</td>
                <td>${transaction.asset_type}</td>
                <td>${transaction.category_name || ''}</td>
                <td>${transaction.cash_amount.toLocaleString()}</td>
                <td>${transaction.cash_cont}</td>
                <td>
                    ${transaction.memo || ''}
                    ${transaction.photo_url ? `<a href="${transaction.photo_url}" target="_blank" title="사진 보기">📷</a>` : ''}
                </td>
            `;
            recordList.appendChild(row);
        });
        bindMasterCheckbox(); // Re-bind checkboxes for new rows
        updateAlertBar(); // Update alert bar based on new rows
    }

    // Function to update the search results display
    function updateSearchResultsDisplay(count, startDate, endDate) {
        const searchResultsContainer = document.querySelector(".search-results-container");
        const searchCountSpan = document.getElementById("search-count");
        const searchPeriodSpan = document.querySelector(".search-period");
        const searchStartDateSpan = document.getElementById("search-start-date");
        const searchEndDateSpan = document.getElementById("search-end-date");

        if (count > 0) {
            // searchResultsContainer.style.display = "flex"; // Keep hidden as per user request
            searchCountSpan.textContent = count;
            searchStartDateSpan.textContent = startDate ? startDate.replace(/-/g, '.') : 'N/A';
            searchEndDateSpan.textContent = endDate ? endDate.replace(/-/g, '.') : 'N/A';
            searchPeriodSpan.style.display = "block"; // Show period if dates are present
        } else {
            searchResultsContainer.style.display = "none";
            searchPeriodSpan.style.display = "none";
        }
    }

    // Initial load or reset search
    async function loadDefaultTransactions() {
        try {
            const response = await fetch('/accbook/search_transactions/'); // Fetch all transactions
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            renderTransactions(data.transactions);
            document.querySelector(".search-results-container").style.display = "none"; // Hide search results
        } catch (error) {
            console.error("Error loading default transactions:", error);
            alert("거래 내역을 불러오는 중 오류가 발생했습니다.");
        }
    }

    // Modify searchResetBtn to also clear search results and load default transactions
    if (searchResetBtn) {
        searchResetBtn.addEventListener("click", () => {
            searchStartDateInput.value = "";
            searchEndDateInput.value = "";
            searchAmountInput.value = "";
            searchExpenseBtn.classList.remove("active");
            searchIncomeBtn.classList.remove("active");
            selectedSearchType = null;
            searchCategorySelect.style.display = 'none'; // Hide dropdown
            searchCategorySelect.value = ""; // Reset selected value
            console.log("Search form reset. Loading default transactions.");
            loadDefaultTransactions(); // Load all transactions
        });
    }

    // Initial load of transactions when the page loads
    console.log("home.js: Initializing...");
    loadDefaultTransactions();
});

// Global error handler to catch any uncaught errors
window.addEventListener('error', (event) => {
    console.error("home.js: Uncaught error detected:", event.error);
    // Optionally, display a user-friendly message or log to a server
});
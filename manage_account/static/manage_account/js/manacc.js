document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('accountCreateForm');
    if (!form) return; // 이 페이지에 해당 폼이 없으면 아무것도 하지 않음

    // 필요한 모든 DOM 요소를 미리 찾아둡니다.
    const accNumInput = document.querySelector('[name="acc_num"]');
    const accNumError = document.getElementById('acc_num_error');
    const passwordField = document.getElementById('id_acc_pw');
    const confirmPasswordInput = document.getElementById('acc_pw_confirm');
    const passwordErrorDiv = document.getElementById('password_match_error');

    let isAccNumTaken = false; // 계좌번호 중복 상태를 저장할 변수

    // --- 1. 계좌번호 중복 확인 (입력 필드를 벗어났을 때) ---
    if (accNumInput && accNumError) {
        accNumInput.addEventListener('blur', function() {
            const accNum = this.value;

            if (accNum.length > 0) {
                fetch(`/manacc/check-acc-num/?acc_num=${accNum}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.is_taken) {
                            accNumError.textContent = '이미 존재하는 계좌번호입니다.';
                            isAccNumTaken = true;
                        } else {
                            accNumError.textContent = '';
                            isAccNumTaken = false;
                        }
                    })
                    .catch(error => {
                        console.error('Error checking account number:', error);
                        accNumError.textContent = '오류가 발생했습니다. 다시 시도해주세요.';
                    });
            } else {
                accNumError.textContent = '';
                isAccNumTaken = false;
            }
        });
    }

    // --- 2. 폼 제출 시 최종 유효성 검사 (하나의 리스너로 통합) ---
    form.addEventListener('submit', function(event) {
        // 비밀번호 일치 여부 확인
        const password = passwordField ? passwordField.value : '';
        const confirmPassword = confirmPasswordInput ? confirmPasswordInput.value : '';
        let passwordMismatch = false;
        
        if (password !== confirmPassword) {
            if(passwordErrorDiv) passwordErrorDiv.textContent = '비밀번호가 다릅니다';
            passwordMismatch = true;
        } else {
            if(passwordErrorDiv) passwordErrorDiv.textContent = '';
        }

        // 계좌번호가 중복되었거나, 비밀번호가 일치하지 않으면 폼 제출을 막음
        if (isAccNumTaken || passwordMismatch) {
            event.preventDefault(); // 폼 제출 중단
            
            if (isAccNumTaken) {
                alert('이미 존재하는 계좌번호입니다. 다른 번호를 입력해주세요.');
            } else if (passwordMismatch) {
                alert('비밀번호가 일치하지 않습니다.');
            }
        }
    });
});
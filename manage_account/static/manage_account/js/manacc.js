document.getElementById('accountCreateForm').addEventListener('submit', function(event) {
    var passwordField = document.getElementById('id_acc_pw');
    var password = passwordField ? passwordField.value : '';
    var confirmPassword = document.getElementById('acc_pw_confirm').value;
    var errorMessageDiv = document.getElementById('password_match_error');

    if (password !== confirmPassword) {
        event.preventDefault();
        errorMessageDiv.textContent = '비밀번호가 다릅니다';
    } else {
        errorMessageDiv.textContent = ''; // Clear the error message if passwords match
    }
});
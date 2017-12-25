
function login(username, password) {
    var data = {};
    data['username'] = username;
    data['password'] = password;
    data['login'] = '';
    $.post('/login', data, function (resp) {
        if (!resp['success']) {
            alert(resp['status']);
        } else {
            window.location = '/';
        }
    }, 'json')
}
$(document).ready(function() {
    $('#login').submit(function(event){
        var username = event.currentTarget[0].value;
        var password = event.currentTarget[1].value;
        login(username, password);

       return false;
    });
});
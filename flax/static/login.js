function register(username, email, password) {
    var data = {};
    data['username'] = username;
    data['email'] = email;
    data['password'] = password;
    data['register'] = '';
    $("#flash").remove();
    $.post('/register', data, function (resp) {
        if (!resp['success']) {
            var status = resp['status'];
            if (status) {
                alert(status);
            } else {
                alert("Something went wrong. Are you already registered with a password?");
            }
        } else {
            $('div#registration_form').prepend($('<p>').html("<a href=\"/\">Account created successfully, login here</a>").attr('id', 'flash'));
        }
    }, 'json');

}

function login(username, password) { // TODO One click
    var data = {};
    data['username'] = username;
    data['password'] = password;
    data['login'] = '';
    $('#flash').remove();
    $.post('/login', data, function (resp) {
        if (!resp['success']) {
            var status = resp['status'];
            if (status) {
                $('div#login_form').prepend($('<p>').text(status).attr('id', 'flash'));
            } else {
                $('div#login_form').prepend($('<p>').text("You shouldn't be seeing this. Reload your page.").attr('id', 'flash'));
            }
        } else {
            $('div#login_form').prepend($('<p>').text("Logging you in...").attr('id', 'flash'));
            window.location = '/';
        }
    }, 'json');
}


$(document).ready(function () {
    $('#login').submit(function (event) {
        var username = event.currentTarget[0].value;
        var password = event.currentTarget[1].value;
        login(username, password);

       return false;
    });

    $("#register").submit(function (event) {
        var username = event.currentTarget[0].value;
        var email = event.currentTarget[1].value;
        var password = event.currentTarget[2].value;
        register(username, email, password);

        return false;
    });
});
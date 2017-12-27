function prepend_flash(flash, flash_div, id) {
    var para = 'p#' + id;
    $(para).remove();
    flash_div.prepend($('<p>').text(flash).attr('id', id));
}

function register(username, email, password) {
    var data = {};
    data['username'] = username;
    data['email'] = email;
    data['password'] = password;
    data['register'] = '';
    var div = $("#registration");
    $.post('/register', data, function (resp) {
        if (!resp['success']) {
            var flash = '';
            var status = resp['status'];
            if (status) {
                flash = status;
                prepend_flash(flash, div, 'registration_flash');
            } else {
                flash = "Something went wrong. Are you already registered with a password?";
                prepend_flash(flash, div, 'registration_flash');
            }
        } else {
            flash = "Account created successfully";
            prepend_flash(flash, div, 'registration_flash');
            window.location = '/';
        }
    }, 'json');
}


function one_click_login(username) { // TODO DRY
    var data = {};
    data['username'] = username;

    var div = $("div#oneclick");
    $.post('/oneclick', data, function (resp) {
        if (!resp['success']) {
            var flash = '';
            var status = resp['status'];
            if (status) {
                flash = status;
                prepend_flash(flash, div, 'oneclick_flash');
            } else {
                flash = "Something went wrong. Are you already registered with a password?";
                prepend_flash(flash, div, 'oneclick_flash');
            }
        } else {
            flash = "Logging you in...";
            prepend_flash(flash, div, 'oneclick_flash');
            window.location = '/';
        }
    }, 'json');

}


function login(username, password) { // TODO One click
    var data = {};
    data['username'] = username;
    data['password'] = password;
    data['login'] = '';

    var div = $("div[id='login']");

    $.post('/login', data, function (resp) {
        if (!resp['success']) {
            var flash = '';
            var status = resp['status'];
            if (status) {
                flash = status;
                prepend_flash(flash, div, 'login_flash');
            } else {
                flash = "You shouldn't be seeing this. Reload your page.";
                prepend_flash(flash, div, 'login_flash');
            }
        } else {
            flash = "Logging you in...";
            prepend_flash(flash, div, 'login_flash');
            // Block form
            window.location = '/';
        }
    }, 'json');
}


$(document).ready(function () {  // Can literally hold down button and spam this pls ratelimit
    $('#login_form').submit(function (event) {
        var username = event.currentTarget[0].value;
        var password = event.currentTarget[1].value;
        login(username, password);

       return false;
    });

    $('#oneclick_form').submit(function (event) {
        var username = event.currentTarget[0].value;
        one_click_login(username);

       return false;
    });

    $("#registration_form").submit(function (event) {
        var username = event.currentTarget[0].value;
        var email = event.currentTarget[1].value;
        var password = event.currentTarget[2].value;
        register(username, email, password);

        return false;
    });
});
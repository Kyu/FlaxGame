/**
 * Created by P.O on 7/29/2017.
 * Filename: game.js
 */

// String Formatting
if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] !== 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

function logout() {
    window.location = '/';
}


function get_my_info() {
    $.get('/game/info/my_info', function(player) {
        $("h4#actions").text("Actions: {0}".format(player['actions']));
        $("h4#ammo").text("Ammo: {0}".format(player['ammo']));
        $("h4#morale").text("Morale: {0}".format(player['morale']));
        $("h4#team").html("Team: <a href=\"/team/{0}\">{0}</a>".format(player['team']));
        $("h4#squad").text("Squad: {0}".format(player['squad']));
        $("h4#troops").text("Troops: {0}".format(player['troops']));
        $("h4#location").html("Located at: <a href=\"/game/{0}\">{0}</a>".format(player['location']));
        $("h6#currently_online").text("Currently online: {0}".format(player['currently_online']));
    }, 'json');
}


function add_action_btns() {
    var recruit_form = $('<form>').attr('action', '/game/action/recruit').attr('method', 'post')
        .append($('<button>').attr('id', 'recruit').text("Recruit!")
        ),
    ammo_form = $('<form>').attr('action', '/game/action/ammo').attr('method', 'post')
        .append($('<button>').attr('id', 'take_ammo').text("Take ammo!")
        ),
    industry_form = $('<form>').attr('action', '/game/action/industry').attr('method', 'post')
        .append($('<button>').attr('id', 'industry').text("Upgrade industry!")
        ),
    infrastructure_form = $('<form>').attr('action', '/game/action/infrastructure').attr('method', 'post')
        .append($('<button>').attr('id', 'infrastructure').text("Upgrade infrastructure!")
        ),
    dig_in_form = $('<form>').attr('action', '/game/action/dig_in').attr('method', 'post')
        .append($('<button>').attr('id', 'dig_in').text("Dig in!")
        );
    var pop = $('h4#population'),
        a_ammo = $('h4#available_ammo'),
        industry = $('h4#industry'),
        inf = $('h4#infrastructure'),
        dug = $('h4#dug_in');

    $('button#recruit').length ? void(0) : pop.after(recruit_form);
    $('button#take_ammo').length ? void(0) : a_ammo.after(ammo_form);
    $('button#industry').length ? void(0) : industry.after(industry_form);
    $('button#infrastructure').length ? void(0) : inf.after(infrastructure_form);
    $('button#dig_in').length ? void(0) : dug.after(dig_in_form);
}


function remove_action_btns() {
    var recruit_btn = $('button#recruit'),
                    take_ammo_btn = $('button#take_ammo'),
                    industry_btn = $('button#industry'),
                    infrastructure_btn = $('button#infrastructure'),
                    dig_in_btn = $('button#dig_in');

    recruit_btn.length ? $(recruit_btn[0].parentNode).remove() : void(0);
    take_ammo_btn.length ? $(take_ammo_btn[0].parentNode).remove() : void(0);
    industry_btn.length ? $(industry_btn[0].parentNode).remove() : void(0);
    infrastructure_btn.length ? $(infrastructure_btn[0].parentNode).remove() : void(0);
    dig_in_btn.length ? $(dig_in_btn[0].parentNode).remove() : void(0);
}


function create_sidebar_right() {
    // check for div#sidebar-left
    $("div#sidebar-left").after(
        $('<div>').attr('id', 'sidebar-right').addClass('sidebar').addClass('navbar-right')
    );
}


function create_hex_div() {
    var sidebar_right = $('div#sidebar-right');
    if (!sidebar_right.length) {
        create_sidebar_right();
        sidebar_right = $('div#sidebar-right');
    }

    sidebar_right.append(
        $('<div>').addClass('hex')
    );
}


function create_here_div() {
    var hex_div = $('div.hex');
    if (!hex_div.length) {
        create_hex_div();
        hex_div = $('div.hex');
    }

    hex_div.append( // why not also_here
        $('<div>').attr('id', 'also-here').append(
            $('<h2>').text("Currently here:")
        )
    );
}


function create_sidenav() { // Return the side nav?
    var here_div = $("div#also-here");
    if (!here_div.length) {
        create_here_div();
        here_div = $("div#also-here");
    }

    here_div.append(
        $('<div>').addClass('sidebar-nav')
    );

}


function populate_amount_players(all_here) {
    var side_nav = $('div.sidebar-nav');
    if (!side_nav.length) {
        create_sidenav();
        side_nav = $('div.sidebar-nav');
    }
    $('p#troops_here_count').remove();
    for (var ih = 0; ih < all_here.length; ih++) {
        side_nav.prepend($('<p>').attr('id', 'troops_here_count').text(all_here[ih])
        );
    }
}


function populate_sidebar_players (players) {

    if (!players || !players.length) {
        return;
    }
    var sidenav = $('div.sidebar-nav');
    if (!sidenav.length) {
        create_sidenav();
        sidenav = $('div.sidebar-nav');
    }
    $('div#also-here').prepend(
        $('<h2>').text("Currently here:")
    );
    for (var i = 0; i < players.length; i++) {
        var cur = players[i];

        sidenav.append($('<li>')
            .append($('<div>').attr('id', 'player_here_also')
                .append($('<p>').text(cur['name']))
                .append($('<p>').text("Squad type: " + cur['squad']))
                .append($('<p>').html("Team: <a href=\"/team/" + cur['team'] + "\">" + cur['team'] + "</a>"))
                .append($('<p>').text("Troops: " + cur['troops']))
                .append($('<p>').text("Morale: " + cur['morale']))
                .append($('<p>').text("Dug in: " + cur['dug_in'] + "%"))
                .append(function () {
                    if (cur['is_enemy']) {
                        return ($('<form>')
                            .attr('action', '/game/action/attack').attr('method', 'post')
                            .append($('<button>')
                                .attr('id', 'attack').attr('name', 'player_called').attr('value', cur['name'])
                                .text("Attack!")
                            ));
                    }
                })
            ));
    }

}


function populate_sidebar(location) {
    var sidebar = $("div#sidebar-right");
    var sidebar_exists = !!sidebar.length;
    if (!sidebar_exists) {
        create_hex_div();
    }

    var loc_html = "Location: <a href=\"/game/" + location['name'] + "\">" + location['name'] + "</a>",
        terrain_text = "Terrain: " + location['terrain'],
        pop_text = "Population: " + location['population'],
        ammo_text = "Available ammo: " + location['ammo'],
        industry_text = "Industry: " + location['industry'],
        infrastructure_text = "Infrastructure: " + location['infrastructure'],
        inf_dom = $('h4#infrastructure');

    if (sidebar_exists) {
        $('h3#this_location').html(loc_html);
        $('h3#terrain').text(terrain_text);
        $('h4#population').text(pop_text);
        $('h4#available_ammo').text(ammo_text);
        $('h4#industry').text(industry_text);
        inf_dom.text(infrastructure_text);
    } else {
        $('div.hex').append(
            $('<h3>').attr('id', 'this_location').html(loc_html)).append(
            $('<h3>').attr('id', 'terrain').text(terrain_text)).append(
            $('<h4>').attr('id', 'population').text(pop_text)).append(
            $('<h4>').attr('id', 'available_ammo').text(ammo_text)).append(
            $('<h4>').attr('id', 'industry').text(industry_text)).append(
            $('<h4>').attr('id', 'infrastructure').text(industry_text)
        );
        inf_dom = $('h4#infrastructure');
    }

    var here_dom = $('h3#is_here'),
        dug = $('h4#dug_in');

    if (location['is_here']) {
        var dug_in_text = "Dug in: " + location['dug_in'] + "%";

        if (!dug.length) {
            inf_dom.after($('<h4>').attr('id', 'dug_in').text(dug_in_text));
            dug = $('h4#dug_in');
        } else {
            dug.text(dug_in_text);
        }

        if (here_dom.length) {
            here_dom.text("You are here!");
        } else {
            dug.after(
                $('<h3>').text("You are here!").attr('id', 'is_here')
            );
        }

        if (location['friendly']) {
            add_action_btns();
        } else {
            remove_action_btns();
        }

    } else {
        remove_action_btns();
        here_dom.remove();
        dug.remove();
        // $("div.sidebar-nav li").remove();
        $("div#also-here").html("");
    }
    populate_sidebar_players(location['also_here']);

    var move_btn = $('#move_here');
    if (location['movable']) {
        if (move_btn.length) {
            move_btn.val(location['name']);
        } else {
            var move_form = $('<form>').attr('method', 'post').attr('action', '/game/action/go_to')
                .append($('<button>').attr('id', 'move_here').attr('name', 'position').attr('value', location['name'])
                    .text("Move Here!"));
            inf_dom.after(move_form);
        }
    } else if (move_btn.length) {
        move_btn[0].form.remove();
    }

    var all_here = location['amount_here'];
    populate_amount_players(all_here);



}


function get_current_location_info() {
    var current_location = $(location).attr('pathname').replace('/game/', '');
    var data = {};
    data['location'] = current_location;
    $.get('/game/info/current_loc_info', data, populate_sidebar, 'json');
}


function update_location(update) {
    var name = update['name'];
    var tb_element = $('td[id="loc_' + name + '"]');
    var title = update['name'] + " - " + update['type'] + update['title'];
    tb_element.attr('title', title).removeClass(
        function (index, className) {
            return (className.match (/(^|\s)location-\S+/g) || []).join(' '); //
        }).addClass('location-' + update['type']);
    if (update['control'] !== 'None') {
        tb_element.addClass('location-' + update['control']);
    }

}


function get_location_info_called(name) {
    var data = {};
    data['location'] = name;

    $.get('/game/info/map', data, function(locations) {
        for (var i = 0; i < locations['locations'].length; i++) {
            update_location(locations['locations'][i]);

}
    }, 'json');

}


function get_new() {
    setTimeout(function () {
        get_my_info();
        get_current_location_info();
        get_location_info_called('all')
    }, 1000);

}


function slideUpAndRemoveAfter(element, time) {
    setTimeout(function () {
        element.slideUp("slow", "linear", function() {element.remove();});
    }, time);
}


function do_action(action) {
    if (action.action === 'movement' && action['succeed']) {
        history.pushState("", "", "/game/" + action['new']);
    }
    var flash_div = $('div#flash');
    var add = $('<p>').text(action.result).addClass('action-notification');
    if (flash_div.length) {
        flash_div.prepend(add);
    } else {
        $("div#sidebar-right").prepend($('<div>').attr('id', 'flash'));
        flash_div = $('div#flash');
    }
    flash_div.prepend(add);
    get_new();
    slideUpAndRemoveAfter(add, 20000);
}


function send_message(message) { // TODO ws://? Maybe?
    var add = $('<p>').text(message['status']).addClass('action-notification');  // message-notification?
    $($("div#messages")[0].children[0]).after(add);
    if (message['success']) {
        $("ul#message-list").append(
            $('<li>').addClass('message')
                .append($("<p>").text("You: " + message['message']['content']).addClass('message-text'))
                .append($("<p>").text(message['message']['timestamp']).addClass('message-timestamp'))
        );
    }
    slideUpAndRemoveAfter(add, 20000);
}

// TODO Minify
$(document).ready(function() {
    $('#take_ammo, #recruit, #industry, #infrastructure, #dig_in, #move_here, #attack').click(function(event){
        event.preventDefault();
        var data = {};
        if (event.currentTarget.name) {
            data[event.currentTarget.name] = event.currentTarget.value
        }
       $.post(event.currentTarget.form.action, data,  do_action, 'json');

       return false;
    });

    $('#send_message').click(function(event) {
        event.preventDefault();
        var data = {};
        data[event.currentTarget.form[0].name] = event.currentTarget.form[0].value;
        $.post(event.currentTarget.form.action, data, send_message, 'json');
        return false;
    });

    $("table#map a").click(function(event) {
        event.preventDefault();
        history.pushState("", "", "/game/" + event.target.text);
        setTimeout(function () {
            get_new();
        }, 500);
        return false;
    });

    $("#logout").click(function(event){
        event.preventDefault();
       $.post("/logout", {}, logout, 'json');
       return false;
    });

});

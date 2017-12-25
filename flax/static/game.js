/**
 * Created by P.O on 7/29/2017.
 * Filename: game.js
 * TODO do this all with JS
 * TODO Ever heard about divs
 */
function get_my_info() {
    $.get('/game/info/my_info', function(player) {
        $("h4#actions").text("Actions: " + player.actions);
        $("h4#ammo").text("Ammo: " + player.ammo);
        $("h4#morale").text("Morale: " + player.morale);
        // $("h4#team").html('Team: <a href="/team/' + player.team + '">' + player.team + '</a>');
        $("h4#squad").text("Squad: "  + player.squad);
        $("h4#troops").text("Troops: " + player.troops);
        // TODO text formatter smh
        // TODO currently online update
        // TODO hex info update
        $("h4#location").html("Located at: <a href=\"/game/" + player.location + "\">" + player.location + "</a>");
    }, 'json');
}


function get_current_location_info() {
    var c_location = $(location).attr('pathname').replace('/game/', '');
    var data = {};
    data['location'] = c_location;
    $.get('/game/info/current_loc_info', data, function(here) {
        $('h3#this_location').html("Location: <a href=\"/game/" + here['name'] + "\">" + here['name'] + "</a>");
        $('h3#terrain').text("Terrain: " + here.terrain);
        var pop = $('h4#population').text("Population: " +  here.population);
        var a_ammo = $('h4#available_ammo').text("Available ammo: " + here.ammo);
        var industry = $('h4#industry').text("Industry: " + here.industry);
        var inf = $('h4#infrastructure').text("Infrastructure: " + here.infrastructure);
        var dug = $('h4#dug_in');
        dug.text("Dig in: " + here.dug_in + "%");
        var here_dom = $('h3#is_here');
        if (here.is_here) {
            if (here_dom.length) {
                here_dom.text("You are here!");
            } else {
                var add = $('<h3>You are here!</h3>');
                add.attr('id', 'is_here');
                dug.after(add);
            }
            var move_btn = $('#move_here');
            if (move_btn.length) {
                move_btn[0].form.remove();
            }

            if (here.friendly) {
                // TODO remove player info if not here
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
                $('button#recruit').length ? void(0) : pop.after(recruit_form);
                $('button#take_ammo').length ? void(0) : a_ammo.after(ammo_form);
                $('button#industry').length ? void(0) : industry.after(industry_form);
                $('button#infrastructure').length ? void(0) : inf.after(infrastructure_form);
                $('button#dig_in').length ? void(0) : dug.after(dig_in_form);
                // TODO text in buttons?
            }

            if (here['amount_here'].length) {
                var here_div = $("div#also-here");
                if (!here_div.length) {
                    here_div = $("<div>");
                    here_div.attr('id', 'also-here').append($('<h2>').text("Currently here:")
                    ).append($('<ul>').addClass('sidebar-nav'))
                }
                here_dom.after(here_div);
                $('[id=player_here_also]').remove();
                $('[id=troops_here_count]').remove();
                for (var i = 0; i < here['also_here'].length; i++) {
                    var cur = here['also_here'][i];
                    var appendage = $('.sidebar-nav')
                        .append($('<ul>').attr('id', 'player_here_also')
                        .append($('<li>').text(cur['name']))
                                .append($('<li>').text("Squad type: " + cur['squad']))
                                .append($('<li>').html("Team: <a href=\"/team/" + cur['team'] + "\">" + cur['team'] + "</a>"))
                                .append($('<li>').text("Troops: " + cur['troops']))
                                .append($('<li>').text("Morale: " + cur['morale']))
                                .append($('<li>').text("Dug in: " + cur['dug_in'] + "%"))
                    );
                    if (cur['is_enemy']) {
                        appendage.append($('<form>').attr('action', '/game/action/attack').attr('method', 'post')
                            .append($('<button>').attr('id', 'attack').attr('name', 'player_called').attr('value', cur[name])
                            ).text("Attack!")
                        );
                    }
                }


                for (var ih = 0; ih < here['amount_here'].length; ih++) {
                    $('.sidebar-nav').prepend($('<li>').attr('id', 'troops_here_count').append($('<p>')
                        .text(here['amount_here'][ih])
                    ));
                }
            }
        } else {
            if (here_dom.length) {
                here_dom.remove();
                dug.remove();
                }
        }
    }, 'json');
}


function update_location(update) {
    var name = update['name'];
    var tb_element = $('td[id="loc_' + name + '"]');
    var title = update['name'] + " - " + update['type'] + update['title'];
    tb_element.attr('title', title).removeClass(
        function (index, className) {
            return (className.match (/(^|\s)location-\S+/g) || []).join(' ');
        }).addClass('location-' + update['type']);
    if (update['control'] !== 'None') {
        tb_element.addClass('location-' + update['control']);
    }

}

// TODO test
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
    }, 2000);

}


function slideUpAndRemoveAfter(element, time) {
    setTimeout(function () {
        element.slideUp("slow", "linear", function() {element.remove();});
    }, time);
}

function do_action(action) {
    if (action.action === 'movement' && action.succeed) {
        history.pushState("", "", "/game/" + action.new);
    }
    var add = $('<p>' + action.result + '</p>');
    add.attr('id', 'flash');
    $("#sidebar-right").append(add);
    get_new();
    slideUpAndRemoveAfter(add, 20000);
}


function send_message(message) {
    var add = $('<p>' + message.message + '</p>');
    add.attr('id', 'flash');
    $($("#messages")[0].children[0]).after(add);
    slideUpAndRemoveAfter(add, 20000);
}


$(document).ready(function() {
    $('#take_ammo, #recruit, #industry, #infrastructure, #dig_in, #move_here, #attack').click(function(event){
        var data = {};
        if (event.currentTarget.name) {
            data[event.currentTarget.name] = event.currentTarget.value
        }
       $.post(event.currentTarget.form.action, data,  do_action, 'json');
       return false;
    });

    $('#send_message').click(function(event) {
        var data = {};
        data[event.currentTarget.form[0].name] = event.currentTarget.form[0].value;
        $.post(event.currentTarget.form.action, data, send_message, 'json');
        return false; // TODO update radio for message
    });

});

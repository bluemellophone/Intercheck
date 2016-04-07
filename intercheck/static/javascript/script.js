
var status_timeout = undefined;
var status_min_interval = 5 * 1000;
var summary_timeout = undefined;
var summary_min_interval = 60 * 60 * 1000;

function force() {
    if( ! $("a#status-force").find("i").hasClass("fa-circle")) {
        console.log("Forcing");
        clearTimeout(status_timeout);
        var request = $.ajax({
            type: "GET",
            url:  "/force/",
        }).error(function() {
            get_status();
        }).success(function(raw) {
            response = $.parseJSON(raw);
            if(response["status"]) {
                $("a#status-force").addClass("forcing");
                $("a#status-force").find("span").html("Forcing...");
                // Make this interval double what the force interval is in Intercheck
                status_timeout = setTimeout(get_status, 2000);
            }
            else {
                update_status_message("Intercheck could not force a SpeedTest", true);
            }
        });
    }
}

function get_status() {
    var request = $.ajax({
        type: "GET",
        url:  "/status/",
    }).error(function() {
        update_status_indicators([]);
    }).success(function(raw) {
        response = $.parseJSON(raw);
        update_status_indicators(response["status"]);
    }).complete(function() {
        status_timeout = setTimeout(get_status, status_min_interval);
    });
}

function get_summary() {
    var request = $.ajax({
        type: "GET",
        url:  "/summary/",
    }).error(function() {
        container.html("ERROR: Could not get summary");
        get_status();
    }).success(function(raw) {
        response = $.parseJSON(raw);
        console.log(response);
        update_summary(response['stats'], response['interval']);
    }).complete(function() {
        summary_timeout = setTimeout(get_summary, summary_min_interval);
    });
}

function update_status_indicators(status) {
    // Update status message
    if($.inArray("init", status) == -1) {
        update_status_message("Cannot connect to Intercheck", true);
    }
    else {
        update_status_message("InterCheck Online", false);
    }
    // Update status circle indicators
    var tags = ["waiting", "testing", "connected", "disconnected"];
    $.each(tags, function( index, tag ) {
        if($.inArray(tag, status) == -1) {
            $("i#status-" + tag).removeClass("fa-circle");
        }
        else {
            $("i#status-" + tag).addClass("fa-circle");
        }
    });

    if($("a#status-force").hasClass("forcing")) {
        $("a#status-force").removeClass("forcing");
        $("a#status-force").find("span").html("Testing");
    }
}

function update_status_message(message, error) {
    var container = $("span#status-message");
    if(error) {
        container.parent().addClass("text-red");
        message = "ERROR: " + message;
    }
    else {
        container.parent().removeClass("text-red");
    }
    container.html(message);
}

function fill_zero(num) {
    if (num < 10) {
        num = "0" + num;
    }
    return num;
}

function update_summary(stats, interval) {
    // Update summary
    var keys = ["ping", "download", "upload", "downtime"];
    $.each(keys, function( index, key ) {
        $("span#summary-" + key).html(stats["30"][key][0])
        $("span#summary-" + key + "-daily").html(stats["1"][key][0])
    });

    $("span#summary-days").each(function() {
        $(this).html(interval);
    });

    var dt = new Date();
    var time = fill_zero(dt.getHours()) + ":" + fill_zero(dt.getMinutes()) + ":" + fill_zero(dt.getSeconds());
    $("span#summary-updated-time").html(time);
}

function init_graphs() {

}

$(document).ready(function() {

    init_graphs();
    get_status();
    get_summary();

    // Init hovers
    $("a#status-force").hover(function() {
        if( ! $(this).hasClass("forcing") && ! $(this).find("i").hasClass("fa-circle")) {
            $(this).find("span").html("Force a SpeedTest");
        }
      },
      function() {
        if( ! $(this).hasClass("forcing")) {
            $(this).find("span").html("Testing");
        }
      }
    );

    // Init links
    $("a#status-force").click(function() {
        force();
        return false;
    });

    $("a#default-settings").click(function() {
        $('input[name^="intercheck-settings-"]').each(function() {
            $(this).attr('use-default', true).change();
        });
        return false;
    });

    $("a#summary-updated").click(function() {
        get_summary();
        return false;
    });

    // Init changes
    $("input[name^='intercheck-settings-']").change(function() {
        var settings_input = $(this);
        var name = settings_input.attr("name");
        var type = settings_input.attr("type");
        if(type == "checkbox") {
            var value = settings_input.is(":checked");
        }
        else {
            var value = settings_input.val();
        }
        if(settings_input[0].hasAttribute('use-default')) {
            settings_input.removeAttr('use-default');
            value = 'default';
        }

        var data = {}
        data[name] = value;
        var container = $("span#intercheck-settings-message");

        var request = $.ajax({
            type: "PUT",
            url:  "/settings/",
            data: data,
        }).error(function() {
            container.html("ERROR: Could not update options");
            get_status();
        }).success(function(raw) {
            response = $.parseJSON(raw);
            var accepted = response["accepted"];
            if(type == "checkbox") {
                settings_input.prop('checked', accepted);
            }
            else {
                settings_input.val(accepted);
            }
            container.html("Updated");
            setTimeout(function() {
                container.html("");
            }, 5000);
        });
    });

    setInterval(function() {
      data = data_speedtest
      data.values = [[1], [1], [1]];
      // increment time 1 step
      data.start = data.start + data.step;
      data.end = data.end + data.step;

      graph_speedtest.slideData(data);
    }, 2000);
});

var API_ENDPOINT = "http://localhost:8080"

// From https://code-maven.com/ajax-request-for-json-data

function ajax_get(url, callback) {
    var xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 && xmlhttp.status == 200) {
            console.log('responseText:' + xmlhttp.responseText);
            try {
                var data = JSON.parse(xmlhttp.responseText);
            } catch(err) {
                console.log(err.message + " in " + xmlhttp.responseText);
                return;
            }
            callback(data);
        }
    };

    xmlhttp.open("GET", url, true);
    xmlhttp.send();
}

ajax_get(API_ENDPOINT + '/meta/heartbeat', function(data) {
	if (data.status) {
		document.getElementById("demo_heartbeat").innerHTML = "Heartbeat success";
	}
	else {
		document.getElementById("demo_heartbeat").innerHTML = "Heartbeat failed";
	}
});

ajax_get(API_ENDPOINT + '/meta/members', function(data) {
	if (data.status) {
        var members = data.result;
        var output = "<p>Team Members:</p><ul>";
        for (var i = 0; i < members.length; i++) {
            output += "<li>" + members[i] + "</li>";
        }
        output += "</ul>";
		document.getElementById("demo_members").innerHTML = output;
	}
	else {
		document.getElementById("demo_members").innerHTML = "Members failed";
	}
});

ajax_get(API_ENDPOINT + '/diary', function(data) {
    if (data.status) {
        var diaries = data.result;
        var output = "<p>Public Diary Entries:</p><ul>";
        for (var i = 0; i < diaries.length; i++) {
            entry = diaries[i];
            temp_date = entry.publish_date;
            publish_date = temp_date.substring(0, 10)
            publish_time = temp_date.substring(11, 16)
            output += "<li>";
            output += "<strong>" + entry.title + "</strong>";
            output += "<br>";
            output += "<small>Written on " + publish_date + " at " + publish_time + "</small>";
            output += "<hr>" + entry.text + "</li>";
        }
        output += "</ul>";
        document.getElementById("demo_diary").innerHTML = output;
    }
    else {
        document.getElementById("demo_diary").innerHTML = "Diary output failed";
    }
});
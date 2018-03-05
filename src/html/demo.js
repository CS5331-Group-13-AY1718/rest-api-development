var API_ENDPOINT = "http://192.168.99.100:8080"

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

function ajax_post(url, jsondata, callback) {
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

    xmlhttp.open("POST", url, true);
    xmlhttp.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
    xmlhttp.send(jsondata);
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
        var output = "<p><h3>Public Diary Entries:</h3></p><ul>";
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

const isValidElement = element => {
  return element.name && element.value;
};

const formToJSON = elements => [].reduce.call(elements, (data, element) => {
  
    if (isValidElement(element)){
        data[element.name] = element.value;
    }
    return data;

}, {});

const handleLoginFormSubmit = event => {
    url = API_ENDPOINT + "/users/authenticate";
    event.preventDefault();
    const data = formToJSON(loginform.elements);
    jsondata = JSON.stringify(data, null, "  ");
    loginform.reset();

    ajax_post(url, jsondata, function(data) {
        if (data.status) {
            document.getElementById("login-feedback").innerHTML = "Login success";
        }
        else {
            document.getElementById("login-feedback").innerHTML = "Login failed";
        }
    });
};

const handleRegisterFormSubmit = event => {
    url = API_ENDPOINT + "/users/register";
    event.preventDefault();
    const data = formToJSON(registerform.elements);
    jsondata = JSON.stringify(data, null, "  ");
    registerform.reset()

    ajax_post(API_ENDPOINT + '/users/register', jsondata, function(data) {
        if (data.status) {
            document.getElementById("register-feedback").innerHTML = "Register success";
        }
        else {
            document.getElementById("register-feedback").innerHTML = "Register failed";
        }
    });
};

const loginform = document.getElementById('login-form');
const registerform = document.getElementById('register-form');
//const data = getFormDataAsJSON(loginform);
loginform.addEventListener('submit', handleLoginFormSubmit);
registerform.addEventListener('submit', handleRegisterFormSubmit);
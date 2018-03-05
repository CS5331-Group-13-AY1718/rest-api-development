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
        var output = "<ul>";
        for (var i = 0; i < diaries.length; i++) {
            entry = diaries[i];
            temp_date = entry.publish_date;
            publish_date = temp_date.substring(0, 10)
            publish_time = temp_date.substring(11, 16)
            output += "<li>";
            output += "<strong>" + entry.title + "</strong>";
            output += "<br>";
            output += "<small>Written by " + entry.author + " on " + publish_date + " at " + publish_time + "</small>";
            output += "<hr>" + entry.text + "</li>";
        }
        output += "</ul><br>";
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
    var loggeduser = data["username"];
    jsondata = JSON.stringify(data, null, "  ");

    ajax_post(url, jsondata, function(data) {
        var result = data.result
        if (data.status) {
            var output = "<input type=\"submit\" value=\"Logout\" onclick=\"userLogOut()\">";
            document.getElementById("login-feedback").innerHTML = "Logged in as " + loggeduser + ". " + output;
            document.getElementById("token").value = data.result.token;
        }
        else {
            document.getElementById("login-feedback").innerHTML = "Login failed";
            document.getElementById("token").value = "";
        }
    });

    loginform.reset();
};

const handleRegisterFormSubmit = event => {
    url = API_ENDPOINT + "/users/register";
    event.preventDefault();
    const data = formToJSON(registerform.elements);
    jsondata = JSON.stringify(data, null, "  ");

    ajax_post(url, jsondata, function(data) {
        if (data.status) {
            document.getElementById("register-feedback").innerHTML = "Successfully registered! Please login to continue.";
        }
        else {
            document.getElementById("register-feedback").innerHTML = "Registration failed.";
        }
    });

    registerform.reset()
};

const retrieveDiarySubmit = event => {
    url = API_ENDPOINT + '/diary'
    event.preventDefault();
    const data = formToJSON(retrievediary.elements);
    jsondata = JSON.stringify(data, null, "  ");
    document.getElementById("my-diaries").innerHTML = "Please log in to view your diary.";

    ajax_post(API_ENDPOINT + '/diary', jsondata, function(data) {
        var diaries = data.result;
        var output = "<ul>";
        for (var i = 0; i < diaries.length; i++) {
            entry = diaries[i];
            temp_date = entry.publish_date;
            publish_date = temp_date.substring(0, 10)
            publish_time = temp_date.substring(11, 16)
            output += "<li>";
            output += "<strong>" + entry.title + "</strong>";
            output += "<br>";
            output += "<small>Written on " + publish_date + " at " + publish_time + "</small>";
            output += "<hr>" + entry.text + "<hr>";
            output += "<span><form method=\"post\" id=\"delete-diary\">";
            output += "<input type=\"hidden\" value=\"" + entry.id + "\" name=\"id\">";
            output += "<input type=\"submit\" value=\"Delete\" class=\"btn btn-danger\" style=\"float: right\"></form></span>";
            output += "</li>";
        }
        output += "</ul>";
        if (data.status) {
            document.getElementById("my-diaries").innerHTML = output;
        }
        else {
            document.getElementById("my-diaries").innerHTML = "Please log in to view your diaries.";
        }
    });
};

const deleteDiarySubmit = event => {
    url = API_ENDPOINT + "/diary/delete";
    event.preventDefault();
    document.getElementById("diary-feedback").innerHTML = "test";
    saved_data = deletediary.elements;
    const data = formToJSON(deletediary.elements);
    jsondata = JSON.stringify(data, null, "  ");

    ajax_post(url, jsondata, function(data) {
        var result = data.result
        if (data.status) {
            document.getElementById("diary-feedback").innerHTML = "Entry deleted";
        }
        else {
            document.getElementById("diary-feedback").innerHTML = "Invalid authentication";
        }
    });
};

const loginform = document.getElementById('login-form');
const registerform = document.getElementById('register-form');
const retrievediary = document.getElementById('retrieve-diary');
const deletediary = document.getElementById('delete-diary');

loginform.addEventListener('submit', handleLoginFormSubmit);
registerform.addEventListener('submit', handleRegisterFormSubmit);
retrievediary.addEventListener('submit', retrieveDiarySubmit);
deletediary.addEventListener('submit', deleteDiarySubmit);

function userLogOut(){
    document.getElementById("token").value = "";
    document.getElementById("my-diaries").innerHTML = "";
    document.getElementById("login-feedback").innerHTML = "";
}

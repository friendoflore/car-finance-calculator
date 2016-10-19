/* Firebase Configuration */
var config = {
  apiKey: "AIzaSyBO7iMzO4xV41v-eEovKR2fHWwQVrK7uPw",
  authDomain: "friendofdata-145422.firebaseapp.com",
  databaseURL: "https://friendofdata-145422.firebaseio.com",
  storageBucket: "friendofdata-145422.appspot.com",
  messagingSenderId: "339745120325"
};
firebase.initializeApp(config);
/* End Firebase Configuration */


/* FirebaseUI Configuration */
var uiConfig = {
  'signInSuccessUrl': '/',
  'signInOptions': [
    // firebase.auth.GoogleAuthProvider.PROVIDER_ID,
    // firebase.auth.FacebookAuthProvider.PROVIDER_ID,
    // firebase.auth.TwitterAuthProvider.PROVIDER_ID,
    // firebase.auth.GithubAuthProvider.PROVIDER_ID,
    firebase.auth.EmailAuthProvider.PROVIDER_ID
  ],
  // Terms of service url.
  'tosUrl': 'https://www.friendofdata.com/'
};

// Initialize the FirebaseUI Widget using Firebase.
var ui = new firebaseui.auth.AuthUI(firebase.auth());

// The start method waits until the DOM is loaded.
ui.start('#firebaseui-auth-container', uiConfig);

$('#firebaseui-auth-container').hide();
/* End FirebaseUI Configuration */


/* Page Variables */
var logOutBtn = $('#log-out_btn');
var logInBtn = $('#log-in_btn');
var displayNameContainer = $('#display-name');
var carInfoContainer = $('#car_info');
var carForm = $('#carForm');
var dataForm = $('#dataForm');
var userIdToken = null;
/* End Page Variables */


window.addEventListener('load', function() {
  initApp()
});


/* Login and Logout Controls */
logOutBtn.click(function(event) {
	event.preventDefault();

	firebase.auth().signOut().then(function() {
		console.log("Sign out successful");

		displayNameContainer.hide();
		window.location = "/";

	}, function(error) {
		console.log(error);
	})
});

logInBtn.click(function(event) {
	$('#firebaseui-auth-container').show();
});
/* End Login and Logout Controls */


/* Firebase inititialization and sign-in listener */
initApp = function() {
  firebase.auth().onAuthStateChanged(function(user) {

    if (user) {
      // User is signed in.
			logOutBtn.removeClass("hidden");
			logInBtn.addClass("hidden");

      var displayName = user.displayName;
      var email = user.email;
      var uid = user.uid;

      user.getToken().then(function(accessToken) {
      	userIdToken = accessToken;
        document.getElementById('display-name').textContent = "Hi, " + displayName;
        listCars();
      });

    } else {
    	logOutBtn.addClass("hidden");
			logInBtn.removeClass("hidden");
			listCars();
    }
  }, function(error) {
    console.log(error);
  });
};


/* Requests stored cars, returns a template carInfoContainer with cars as 
 	 template variables */
function listCars() {
	ajaxForm(carForm, 'GET', '/car');
};

/* Stores car in the DB associated with user if logged in
   Stores car in DB with session if not logged in */
function addCar() {
	ajaxForm(carForm, 'POST', '/car');
};

/* Deletes car from DB with matching key. "key_seq" parameter is the template 
	 order of the form objects (not the car's key sent to the server) */
function deleteCar(key_seq) {
	del_id = "#deleteCarForm" + key_seq
	var deleteForm = $(del_id);
	ajaxForm(deleteForm, 'PUT', '/car');
};

/* Stores data form in the session */
function addData() {
	ajaxForm(dataForm, 'POST', '/data');
};



/* AJAX form submission. On success, renders the response. */
function ajaxForm(form, method, url) {
	jQuery.ajax({
		headers: {
			'Authorization': 'Bearer ' + userIdToken
		},
		type: method,
		url: url,
		data: form.serialize(),
		success: renderCars
	})
};

/* Renders car objects */
function renderCars(data) {
	carInfoContainer.html(data);
};


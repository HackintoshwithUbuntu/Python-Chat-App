// View control buttons
const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
// Stuff on sign up page
const signupuser = document.getElementById("usersignup");
const signuppass = document.getElementById("passsignup");
const sendupbut = document.getElementById('sendsignupbut');
const signeduptxt = document.getElementById('signuptxt');
// Stuff on sign in page
const loginbut = document.getElementById('signinbut');
const loginpass = document.getElementById("passlogin");
const loginuser = document.getElementById('userlogin');
// Other stuff for animations
const container = document.getElementById('container');
var sound = new Audio('loginsnd.mp3');
var switchsnd = new Audio('switchsnd.mp3');

// Click event for switch
signUpButton.addEventListener('click', () => {
	container.classList.add("right-panel-active");
	switchsnd.play();
});

// Other click event for swtich
signInButton.addEventListener('click', () => {
	container.classList.remove("right-panel-active");
	switchsnd.play();
});

// Attempt sign up button click
sendupbut.addEventListener('click', () => {
	// Play sound
	sound.play();
	// Get values
	var username = signupuser.value
	var passw = signuppass.value
	let upfail = document.getElementById("upfail")

	// Communicate with python code to attempt sign up
	async function trysignup(user, passw2){
		// Attempt
		var attempt = await eel.attempt_sign_up(user, passw2)()
		// Log
		console.log(attempt)
		console.log(attempt == true)
	
		// If successful, update
		// if not, show error
		if(attempt == true){
			// add this class if func returns true
			signeduptxt.classList.add("textshow");
			upfail.style.display = "none";	
		}
		else{
			upfail.style.display = "block";
		}}

	// Call the function
	trysignup(username, passw)
});

loginbut.addEventListener('click', () => {
	// Play sound
	sound.play();
	// Get values
	var username = loginuser.value
	var passw = loginpass.value

	// Communicate with python code to attempt sign up
	async function trylogin(user, passw2){
		// Attempt
		var attempt = await eel.attempt_sign_in(user, passw2)()
		// Log
		console.log(attempt)
		console.log(attempt == true)
		let infail = document.getElementById("infail")
		
		// If successful, update
		// if not, show error
		if(attempt == true){
			console.log("YAY");
				// Open the new window 
				// with the URL replacing the
				// current page using the
				// _self value
				// We use this to take ownership of the login window so we can 
				// automatically close it, so that the other chat window
				// can open up in its position as dictated by the python code
				let new_window =
					open(location, '_self');
				// Close this window
				new_window.close();
		}
		else{
			// Make error visible
			infail.style.display = "block";
		}
	}
	// Call the function
	trylogin(username, passw)
});
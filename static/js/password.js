function check_strength(text) {
var meets_min = 1;
var strength = 0;
var minLength = 8;

// reset formatting if the fields are cleared:
if (text.length == 0) {
  password.parentElement.parentElement.className = "form-group";
  format_strength(0, 'Password must be non-empty');
  return;
}
check_confirm_pass(confirm_pass.value);

if (text.length < minLength) {
  format_strength(text.length, 'Password must be at least '+minLength+' characters long');
  password.parentElement.parentElement.className = "form-group has-error";
  return;
}
if (text.search(/[A-Z]/) == -1) {
  format_strength(30, 'Password should contain at least one capital letter');
  password.parentElement.parentElement.className = "form-group has-warning";
  return;
}
if (text.search(/[^a-zA-Z0-9]/) == -1) {
  format_strength(60, 'Password should contain at least one non-alphanumeric character');
  password.parentElement.parentElement.className = "form-group has-warning";
  return;
}

password.parentElement.parentElement.className = "form-group has-success";
strength = 75;

strength += ((text.length - minLength) * 16);

if (strength < 75) {
  format_strength(strength, 'Weak');
} else if (strength < 100) {
  format_strength(strength, 'Medium');
} else if (strength < 150) {
  format_strength(strength, 'Strong');
} else if (strength < 200) {
  format_strength(strength, 'Secure');
} else {
  format_strength(200, 'Very Secure');
}
}

function format_strength(strength, message) {
var level;

if (strength == 0) {
  level = 'progress-bar';
} else if (strength < 50) {
  level = 'progress-bar progress-bar-danger';
} else if (strength < 75) {
  level = 'progress-bar progress-bar-warning';
} else if (strength < 100) {
  level = 'progress-bar progress-bar-info';
} else if (strength < 150) {
  level = 'progress-bar progress-bar-success';
} else {
  level = 'progress-bar progress-bar-success';
}

document.getElementById('secure_bar').className = level;
document.getElementById('secure_bar').style.width = (strength / 2) + '%';
document.getElementById('secure_text').innerHTML = message;
document.getElementById('secure_bar-sr').innerHTML = message;
}

function check_confirm_pass(confirm_val) {
// get original value
if (confirm_val != document.getElementById("password").value) {
  document.getElementById("confirm_text").innerHTML = "Passwords must match.";
  confirm_pass.parentElement.parentElement.className = "form-group has-error";
} else {
  document.getElementById("confirm_text").innerHTML = "";
  confirm_pass.parentElement.parentElement.className = "form-group has-success";
}

if (confirm_val == "")
  confirm_pass.parentElement.parentElement.className = "form-group";
}

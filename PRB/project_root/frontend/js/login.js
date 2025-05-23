// ✅ login.js - اصلاح ذخیره اطلاعات کاربر از توکن

document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  try {
    const response = await fetch("http://localhost:8000/v1/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({ username, password }),
    });

    const result = await response.json();
    if (!response.ok || !result.access_token) {
      alert("❌ ورود ناموفق بود");
      return;
    }

    const token = result.access_token;
    localStorage.setItem("access_token", token);
    localStorage.setItem("token_type", result.token_type);

    const payloadBase64 = token.split(".")[1];
    const decodedPayload = JSON.parse(atob(payloadBase64.replace(/-/g, "+").replace(/_/g, "/")));

    const user = {
      username: decodedPayload.username,
      is_admin: decodedPayload.is_admin,
      is_employer: decodedPayload.is_employer,
    };
    localStorage.setItem("user", JSON.stringify(user));

    if (user.is_admin) {
      window.location.href = "admin.html";
    } else if (user.is_employer) {
      window.location.href = "employer_chat.html";
    } else {
      window.location.href = "home.html";
    }
  } catch (err) {
    alert("⚠️ خطا در ورود: " + err.message);
  }
});


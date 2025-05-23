document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  const phoneRegex = /^09\d{9}$/;
  if (!phoneRegex.test(username)) {
    alert("شماره تلفن معتبر نیست. مثال: 09123456789");
    return;
  }

  if (password.length < 8) {
    alert("رمز عبور باید حداقل ۸ کاراکتر باشد.");
    return;
  }

  try {
    const response = await fetch("http://localhost:8000/v1/login", {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: new URLSearchParams({
        username: username,
        password: password,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      alert("❌ " + (result.detail || "ورود ناموفق بود."));
      return;
    }

    const token = result.access_token;
    const tokenType = result.token_type;

    if (!token) {
      alert("❌ توکن دریافتی نامعتبر است.");
      return;
    }

    // تابع برای دیکد کردن base64url
    function base64UrlDecode(str) {
      str = str.replace(/-/g, "+").replace(/_/g, "/");
      while (str.length % 4) {
        str += "=";
      }
      return atob(str);
    }

    // دیکد JWT
    const payloadBase64 = token.split(".")[1];
    const decodedPayload = JSON.parse(base64UrlDecode(payloadBase64));
    console.log("Decoded JWT payload:", decodedPayload);

    const user = {
      id: parseInt(decodedPayload.sub, 10),  // تبدیل sub به عدد
      username: decodedPayload.username,
      is_admin: decodedPayload.is_admin,
      is_employer: decodedPayload.is_employer,
    };

    localStorage.setItem("access_token", token);
    localStorage.setItem("token_type", tokenType);
    localStorage.setItem("user", JSON.stringify(user));

    alert("✅ ورود موفقیت‌آمیز بود!");

    if (user.is_admin === true || user.is_admin === "true") {
      window.location.href = "admin.html";
    } else if (user.is_employer === true || user.is_employer === "true") {
      window.location.href = "employer_chat.html";
    } else {
      window.location.href = "home.html";
    }

  } catch (error) {
    console.error("Login error:", error);
    alert("⚠️ خطا در ورود: " + error.message);
  }
});

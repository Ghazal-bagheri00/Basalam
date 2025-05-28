document.getElementById("registerForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();
  const first_name = document.getElementById("first_name").value.trim();
  const last_name = document.getElementById("last_name").value.trim();
  const province = document.getElementById("province").value.trim();

  const role = document.querySelector('input[name="role"]:checked')?.value || "user";

  if (!username || !password || !first_name || !last_name || !province) {
    alert("لطفاً همه‌ی فیلدها را کامل وارد کنید.");
    return;
  }

  const phoneRegex = /^09\d{9}$/;
  if (!phoneRegex.test(username)) {
    alert("فرمت شماره همراه معتبر نیست. لطفاً شماره‌ای مانند 09123456789 وارد کنید.");
    return;
  }

  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasNumber = /\d/.test(password);
  if (password.length < 8 || !hasUpper || !hasLower || !hasNumber) {
    alert("رمز عبور باید حداقل ۸ کاراکتر و شامل حروف بزرگ، کوچک و عدد باشد.");
    return;
  }

  const is_admin = false; // Admin role is set via backend
  const is_employer = role === "employer";
  
  const userData = {
    username,
    password,
    first_name,
    last_name,
    province,
    is_admin,
    is_employer,
  };
  
  try {
    const response = await fetch("http://localhost:8000/v1/register", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    });
    
    const result = await response.json();

    if (!response.ok) {
      let message = "ثبت‌نام ناموفق بود.";
      if (result.detail) {
        message = typeof result.detail === "string" ? result.detail : result.detail[0]?.msg || message;
      }
      alert("❌ " + message);
      return;
    }

    alert("✅ ثبت‌نام با موفقیت انجام شد!");
    window.location.href = "login.html";
  } catch (error) {
    alert("⚠️ خطا در ثبت‌نام: " + error.message);
    console.error("Registration error:", error);
  }
});





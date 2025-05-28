document.addEventListener("DOMContentLoaded", async () => {
    const contactsList = document.getElementById("contacts-list");
    const token = localStorage.getItem("access_token");
    const user = JSON.parse(localStorage.getItem('user'));
  
    if (!token || !user || !user.is_employer) {
      contactsList.innerHTML = `<p class="system-msg">❌ لطفاً ابتدا به عنوان کارفرما وارد شوید.</p>`;
      // Redirect to login after a delay
      setTimeout(() => {
          window.location.href = "login.html";
      }, 2000);
      return;
    }
  
    try {
      const res = await fetch(`http://localhost:8000/v1/employer/contacts`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        contactsList.innerHTML = `<p class="system-msg">❌ خطا در دریافت مخاطبین: ${errorData.detail || "خطای ناشناخته"}</p>`;
        console.error("Error fetching contacts:", errorData);
        return;
      }
  
      const users = await res.json();
      if (!users.length) {
        contactsList.innerHTML = `<p class="system-msg">🟡 هنوز پیامی دریافت نکرده‌اید.</p>`;
        return;
      }
  
      contactsList.innerHTML = "";
      users.forEach(user => {
        const div = document.createElement("div");
        div.className = "chat-user-item";
        div.innerHTML = `
          <span>${user.first_name} ${user.last_name}</span>
          <span style="font-size: 0.8em; color: #777;">(${user.username})</span>
        `;
        div.addEventListener("click", () => {
          localStorage.setItem("employer_chat_user_id", user.id);
          window.location.href = "chat.html";
        });
        contactsList.appendChild(div);
      });
    } catch (err) {
      console.error("Fetch error:", err);
      contactsList.innerHTML = `<p class="system-msg">❌ خطا در ارتباط با سرور: ${err.message}</p>`;
    }
  });
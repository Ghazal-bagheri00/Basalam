// frontend/js/chat.js

(() => {
    const API_BASE = "http://localhost:8000/v1"; 
  
    const chatBox = document.getElementById("chat-box");
    const chatHeader = document.getElementById("chat-header"); 
    const messageInput = document.getElementById("message-input");
    const sendButton = document.getElementById("send-button");
  
    let currentUserId = null;
    let receiverId = null;
    let socket = null;
  
    const token = localStorage.getItem("access_token");
    // اینها فقط برای یک بار استفاده از localStorage هستند و بلافاصله پاک می‌شوند
    const employerChatUserId = localStorage.getItem("employer_chat_user_id"); 
    const jobId = localStorage.getItem("job_id");
  
    // بلافاصله پس از خواندن، آیتم‌ها را از localStorage پاک می‌کنیم
    // این کار از ایجاد ریدایرکت‌های ناخواسته در آینده جلوگیری می‌کند
    localStorage.removeItem("employer_chat_user_id"); 
    localStorage.removeItem("job_id"); 
  
    function appendMessage({ sender_id, content, timestamp }) {
      const div = document.createElement("div");
      // تعیین کلاس CSS بر اساس اینکه پیام از طرف کاربر فعلی است یا خیر
      div.className = "chat-message " + (sender_id === currentUserId ? "me" : "other");
      
      // فرمت کردن زمان به صورت خوانا (مثلاً 10:30 ق.ظ)
      const time = new Date(timestamp).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' });
      // نمایش محتوای پیام و زمان ارسال
      div.innerHTML = `<span class="content">${content}</span><span class="timestamp">${time}</span>`; 
      
      // اضافه کردن پیام به باکس چت
      chatBox.appendChild(div);
      // اسکرول کردن به پایین باکس چت برای نمایش جدیدترین پیام
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  
    function appendSystemMessage(text) {
      const p = document.createElement("p");
      p.className = "system-msg"; // کلاس برای پیام‌های سیستمی
      p.textContent = text;
      chatBox.appendChild(p);
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  
    async function fetchWithAuth(url, options = {}) {
      // اگر توکن موجود نیست، درخواست احراز هویت شده را ارسال نکن
      if (!token) throw new Error("توکن احراز هویت موجود نیست. لطفاً وارد شوید.");
  
      const response = await fetch(url, {
        ...options,
        headers: {
          ...options.headers,
          Authorization: `Bearer ${token}`, // ارسال توکن در هدر Authorization
          "Content-Type": "application/json", // معمولاً برای درخواست‌های POST/PUT/PATCH
        },
      });
  
      // بررسی وضعیت پاسخ HTTP
      if (!response.ok) {
        let errorText = await response.text();
        try {
          const errJson = JSON.parse(errorText);
          // اگر جزئیات خطا در response.detail باشد
          if (errJson.detail) {
            // اگر detail یک رشته بود، مستقیماً از آن استفاده کن، در غیر این صورت آن را JSON.stringify کن
            throw new Error(typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail));
          }
          // اگر خطا در response.message باشد
          if (errJson.message) {
            throw new Error(errJson.message);
          }
          throw new Error(JSON.stringify(errJson)); // اگر فرمت ناشناخته‌ای داشت
        } catch {
          throw new Error(errorText || "خطای ناشناخته در ارتباط با سرور."); // اگر نتوانست JSON را parse کند
        }
      }
      return await response.json(); // بازگرداندن پاسخ به فرمت JSON
    }
  
    async function initChat() {
      if (!token) {
        appendSystemMessage("❌ توکن احراز هویت موجود نیست. لطفاً وارد شوید تا بتوانید چت کنید.");
        messageInput.disabled = true;
        sendButton.disabled = true;
        return;
      }
  
      try {
        // دریافت اطلاعات کاربر فعلی از بک‌اند (با استفاده از توکن)
        const me = await fetchWithAuth(`${API_BASE}/user/me`);
        currentUserId = me.id; // اینجا currentUserId باید ID عددی کاربر باشد
  
        let targetUser = null; // اطلاعات کاربر مقصد
        let resolvedReceiverId = null; // شناسه عددی کاربر مقصد
  
        if (employerChatUserId) {
          // اگر کارفرما از لیست مخاطبین چت خود به اینجا آمده است
          // employerChatUserId باید ID عددی کاربر کارجو باشد
          resolvedReceiverId = parseInt(employerChatUserId); // تبدیل به عدد
          if (isNaN(resolvedReceiverId)) {
              throw new Error("شناسه مخاطب چت نامعتبر است.");
          }
          const user = await fetchWithAuth(`${API_BASE}/user/${resolvedReceiverId}`);
          targetUser = user;
        } else if (jobId) {
          // اگر کارجو از صفحه جزئیات شغل به اینجا آمده است
          // jobId باید ID عددی شغل باشد
          const parsedJobId = parseInt(jobId); // تبدیل به عدد
          if (isNaN(parsedJobId)) {
              throw new Error("شناسه شغل نامعتبر است.");
          }
          const job = await fetchWithAuth(`${API_BASE}/jobs/${parsedJobId}`);
          if (!job.employer || !job.employer.id) {
              throw new Error("کارفرما برای این شغل مشخص نشده است. امکان چت وجود ندارد.");
          }
          targetUser = job.employer;
          resolvedReceiverId = job.employer.id;
        } else {
          // اگر نه employerChatUserId و نه jobId موجود باشد، مقصد چت مشخص نیست
          appendSystemMessage("❌ شناسه گیرنده پیام مشخص نیست. لطفاً یک شغل یا مخاطب را برای چت انتخاب کنید.");
          messageInput.disabled = true;
          sendButton.disabled = true;
          return;
        }
        
        // نهایی کردن receiverId پس از تعیین مقصد
        receiverId = resolvedReceiverId;
  
        // اگر targetUser هنوز نامشخص باشد (مثلاً در شرایط خطای خاص)
        if (!targetUser) {
            appendSystemMessage("❌ اطلاعات کاربر مقصد چت قابل بارگذاری نیست.");
            messageInput.disabled = true;
            sendButton.disabled = true;
            return;
        }
  
        // تنظیم عنوان هدر چت
        chatHeader.textContent = `💬 چت با ${targetUser.first_name || "نامشخص"} ${targetUser.last_name || ""}`; 
  
        // بارگذاری پیام‌های قبلی
        const messages = await fetchWithAuth(`${API_BASE}/messages/?receiver_id=${receiverId}`);
        chatBox.innerHTML = ""; // پاک کردن پیام‌های "در حال بارگذاری..."
        if (messages.length === 0) {
          appendSystemMessage("پیامی وجود ندارد. اولین پیام را ارسال کنید!");
        } else {
          messages.forEach(appendMessage);
        }
  
        // راه‌اندازی اتصال WebSocket
        setupWebSocket();
      } catch (err) {
        console.error("Error initializing chat:", err);
        let msg = "خطا در بارگذاری چت. ";
        if (err instanceof Error) {
          msg += err.message;
        } else if (typeof err === "string") {
          msg += err;
        }
        appendSystemMessage(`❌ ${msg}`);
        messageInput.disabled = true;
        sendButton.disabled = true;
      }
    }
  
    function setupWebSocket() {
      // ساخت URL WebSocket با شناسه گیرنده و توکن
      // ws://localhost:8000/v1/messages/ws/chat/{receiver_id}?token={token}
      socket = new WebSocket(`ws://localhost:8000/v1/messages/ws/chat/${receiverId}?token=${token}`);
      
      // Event Listener برای باز شدن اتصال WebSocket
      socket.addEventListener("open", () => {
        appendSystemMessage("✅ اتصال چت برقرار شد.");
        messageInput.disabled = false; // فعال کردن فیلد ورودی پیام
        messageInput.focus(); // فوکوس روی فیلد ورودی
        sendButton.disabled = messageInput.value.trim() === ""; // تنظیم اولیه دکمه ارسال
      });
      
      // Event Listener برای دریافت پیام جدید
      socket.addEventListener("message", event => {
        try {
          const data = JSON.parse(event.data);
          // اگر پیام شامل sender_id و content بود، آن را نمایش بده
          if (data && data.sender_id && data.content) {
            appendMessage(data);
          }
        } catch (e) {
          console.warn("خطا در پردازش پیام دریافتی WebSocket:", e);
        }
      });
      
      // Event Listener برای قطع شدن اتصال WebSocket
      socket.addEventListener("close", () => {
        appendSystemMessage("🔌 اتصال چت قطع شد.");
        messageInput.disabled = true; // غیرفعال کردن فیلد ورودی پیام
        sendButton.disabled = true; // غیرفعال کردن دکمه ارسال
      });
      
      // Event Listener برای خطاهای WebSocket
      socket.addEventListener("error", (err) => {
        console.error("WebSocket error:", err);
        appendSystemMessage("❌ خطا در اتصال وب‌سوکت چت.");
      });
  
      // Event Listener برای ورودی پیام: فعال/غیرفعال کردن دکمه ارسال
      messageInput.addEventListener("input", () => {
        sendButton.disabled = messageInput.value.trim() === "";
      });
      
      // Event Listener برای کلیک روی دکمه ارسال
      sendButton.addEventListener("click", () => {
        sendMessage();
      });
      
      // Event Listener برای زدن کلید Enter در فیلد پیام
      messageInput.addEventListener("keydown", e => {
        // اگر Enter زده شد و Shift فشرده نشده بود و دکمه ارسال فعال بود
        if (e.key === "Enter" && !e.shiftKey && !sendButton.disabled) {
          e.preventDefault(); // جلوگیری از ایجاد خط جدید
          sendMessage(); // ارسال پیام
        }
      });
    }
    
    function sendMessage() {
      const content = messageInput.value.trim(); // گرفتن متن پیام و حذف فاصله‌های اضافی
      // اگر متن خالی بود یا اتصال WebSocket آماده نبود، کاری انجام نده
      if (!content || !socket || socket.readyState !== WebSocket.OPEN) return;
      
      const message = { content }; // ساخت شیء پیام
      socket.send(JSON.stringify(message)); // ارسال پیام از طریق WebSocket (به صورت JSON)
      
      // نمایش پیام خود کاربر بلافاصله در رابط کاربری
      appendMessage({ sender_id: currentUserId, content, timestamp: new Date().toISOString() }); 
      
      messageInput.value = ""; // پاک کردن فیلد ورودی
      sendButton.disabled = true; // غیرفعال کردن دکمه ارسال
      messageInput.focus(); // فوکوس مجدد روی فیلد ورودی
    }
    
    initChat(); // فراخوانی تابع شروع چت هنگام بارگذاری صفحه
  })();
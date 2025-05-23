const BASE_URL = 'http://localhost:8000/v1';
const container = document.getElementById('data-container');

// گرفتن توکن از localStorage
const token = localStorage.getItem('token');

function showData(type) {
  container.innerHTML = '⏳ در حال بارگذاری...';

  let endpoint = '';
  switch(type) {
    case 'city':
      endpoint = 'cities';
      break;
    case 'job':
      endpoint = 'jobs';
      break;
    case 'userjob':
      endpoint = 'user/my-jobs'; // مسیر صحیح از backend
      break;
    default:
      container.innerHTML = 'نوع داده نامعتبر است.';
      return;
  }

  fetch(`${BASE_URL}/${endpoint}`, {
    headers: {
      // اگر توکن وجود داشت اضافه می‌کنیم
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  })
  .then(res => {
    if (!res.ok) throw new Error(`خطا در دریافت داده‌ها: ${res.status}`);
    return res.json();
  })
  .then(data => {
    container.innerHTML = '';
    if (type === 'city') renderCities(data);
    else if (type === 'job') renderJobs(data);
    else if (type === 'userjob') renderUserJobs(data);
  })
  .catch(err => {
    console.error(err);
    container.innerHTML = `<p style="color:red;">❌ خطا: ${err.message}</p>`;
  });
}

// رندر شهرها
function renderCities(cities) {
  if (!cities.length) return (container.innerHTML = 'هیچ شهری یافت نشد.');
  container.innerHTML = '';
  cities.forEach(city => {
    container.innerHTML += `
      <div class="card">
        <h3>شهر: ${city.name}</h3>
      </div>`;
  });
}

// رندر شغل‌ها
function renderJobs(jobs) {
  if (!jobs.length) return (container.innerHTML = 'هیچ شغلی یافت نشد.');
  container.innerHTML = '';
  jobs.forEach(job => {
    container.innerHTML += `
      <div class="card">
        <h3>شغل: ${job.name}</h3>
      </div>`;
  });
}

// رندر درخواست‌های شغلی
function renderUserJobs(userjobs) {
  if (!userjobs.length) return (container.innerHTML = 'هیچ درخواستی وجود ندارد.');
  container.innerHTML = '';
  userjobs.forEach(req => {
    container.innerHTML += `
      <div class="card">
        <h3>کاربر: ${req.user_id} → شغل: ${req.job_id}</h3>
      </div>`;
  });
}



const money=n=>"₹"+Number(n||0).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2});
let chart;
async function api(url,opt){const r=await fetch(url,opt);return r.json()}
async function load(){
 const d=await api("/api/dashboard");
 document.getElementById("income").textContent=money(d.income);
 document.getElementById("expense").textContent=money(d.expense);
 document.getElementById("balance").textContent=money(d.balance);
 document.getElementById("budget").textContent=money(d.budget);
 document.getElementById("recommendations").innerHTML=d.recommendations.map(x=>`<div class="rec">💡 ${x}</div>`).join("");
 if(chart)chart.destroy();
 chart=new Chart(document.getElementById("chart"),{type:"doughnut",data:{labels:d.categories.map(x=>x.category),datasets:[{data:d.categories.map(x=>x.total)}]},options:{responsive:true}});
 const t=await api("/api/transactions");
 document.getElementById("transactions").innerHTML=t.map(x=>`<tr><td>${x.date}</td><td class="${x.type}">${x.type}</td><td>${x.category}</td><td>${money(x.amount)}</td><td>${x.note||"-"}</td><td><button class="delete" onclick="removeTx(${x.id})">Delete</button></td></tr>`).join("");
 const s=await api("/api/settings");
 document.getElementById("monthlyIncome").value=s.monthly_income||"";
 document.getElementById("monthlyBudget").value=s.monthly_budget||"";
}
document.getElementById("transactionForm").addEventListener("submit",async e=>{
 e.preventDefault();
 await api("/api/transactions",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
 type:document.getElementById("type").value,category:document.getElementById("category").value,
 amount:document.getElementById("amount").value,note:document.getElementById("note").value,date:document.getElementById("date").value
 })});
 e.target.reset();load();
});
document.getElementById("settingsForm").addEventListener("submit",async e=>{
 e.preventDefault();
 await api("/api/settings",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
 monthly_income:document.getElementById("monthlyIncome").value,monthly_budget:document.getElementById("monthlyBudget").value
 })});load();
});
async function removeTx(id){await api("/api/transactions/"+id,{method:"DELETE"});load()}
load();

async function refreshAgents() {
  const res = await fetch('/agents/list');
  const data = await res.json();
  const list = document.getElementById('agent-list');
  list.innerHTML = '';
  (data.agents || []).forEach(a=> {
     const li = document.createElement('li');
     li.textContent = a;
     list.appendChild(li);
  });
}

async function createAgent(e){
  e.preventDefault();
  const id = document.getElementById('agentId').value;
  const cap = JSON.parse(document.getElementById('capabilities').value);
  const cls = document.getElementById('className').value;
  const res = await fetch('/agents/create',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:id,capabilities:cap,agent_class:cls})});
  const js=await res.json();
  alert(JSON.stringify(js));
  refreshAgents();
}

async function deleteAgent(e){
  e.preventDefault();
  const id=document.getElementById('deleteAgentId').value;
  const res=await fetch('/agents/delete',{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:id})});
  const js=await res.json();
  alert(JSON.stringify(js));
  refreshAgents();
}

async function submitTask(e){
  e.preventDefault();
  const skill=document.getElementById('skill').value;
  const taskId=document.getElementById('taskId').value;
  const data=JSON.parse(document.getElementById('taskData').value);
  const res=await fetch('/task',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill,task_id:taskId,data})});
  const js=await res.json();
  document.getElementById('taskResult').textContent = JSON.stringify(js);
}

window.onload = refreshAgents;
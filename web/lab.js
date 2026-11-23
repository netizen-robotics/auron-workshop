import RFB from "./core/rfb.js";

const byId = (id) => document.getElementById(id);
const turtleSelect = byId("turtle");
const connection = byId("connection");
const activity = byId("activity");
const picker = byId("picker");
const driveTools = byId("drive-tools");
const actionTools = byId("action-tools");
const actionList = byId("action-list");
const rotationType = "turtlesim/action/RotateAbsolute";
const tabs = [...document.querySelectorAll('[role="tab"]')];
const settings = byId("settings");
const parameterList = byId("parameter-list");
const parameterTools = byId("parameter-tools");
const parameterEdit = byId("parameter-edit");
const cancelButton = byId("cancel");
const bridgeUrl = "ws://127.0.0.1:9090";
const pendingServices = new Map();
const advertised = new Set();
const poseFields = {
  x: "pose-x",
  y: "pose-y",
  theta: "pose-theta",
  linear_velocity: "pose-linear",
  angular_velocity: "pose-angular",
};
const backgroundParameters = ["background_r", "background_g", "background_b"];
const parameterDescriptions = {
  background_r: "Red channel of the background. Choose an integer from 0 to 255.",
  background_g: "Green channel of the background. Choose an integer from 0 to 255.",
  background_b: "Blue channel of the background. Choose an integer from 0 to 255.",
  holonomic: "Enable sideways movement with Q and E or the Strafe buttons in Topics.",
};
const parameterTypes = [
  ["not set"], ["boolean", "bool_value"], ["integer", "integer_value"],
  ["double", "double_value"], ["string", "string_value"], ["byte array", "byte_array_value"],
  ["boolean array", "bool_array_value"], ["integer array", "integer_array_value"],
  ["double array", "double_array_value"], ["string array", "string_array_value"],
];
const parameterValues = new Map();
const keyboardMoves = {
  ArrowUp: [1, 0, 0],
  ArrowDown: [-1, 0, 0],
  ArrowLeft: [0, 0, 1.5],
  ArrowRight: [0, 0, -1.5],
  q: [0, 1, 0],
  e: [0, -1, 0],
};

let ws;
let nextId = 0;
let selectedTurtle = "";
let followTopics = [];
let driving;
let rotation;
let activeTab = "topics";
let commandCount = 0;
let lastMovement;

function trace(summary, details) {
  const json = details.querySelector("pre");
  let messages;
  const showJson = () => {
    if (details.open) json.textContent = JSON.stringify(messages, null, 2);
  };
  details.addEventListener("toggle", showJson);
  return (text, packets) => {
    summary.textContent = text;
    messages = packets;
    details.hidden = !messages;
    showJson();
  };
}

const showCommand = trace(byId("command-summary"), byId("command-details"));
const topicStreams = [
  {
    name: "cmd_vel", type: "geometry_msgs/msg/Twist",
    label: "velocity", show: trace(byId("velocity-summary"), byId("velocity-details")),
    summarize: velocitySummary,
  },
  {
    name: "pose", type: "turtlesim/msg/Pose",
    label: "pose", show: trace(byId("pose-summary"), byId("pose-details")),
    summarize(message) {
      for (const [field, id] of Object.entries(poseFields)) {
        byId(id).textContent = message[field].toFixed(2);
      }
      const { x, y, theta } = message;
      return "X " + x.toFixed(2) + ", Y " + y.toFixed(2) + ", heading " + theta.toFixed(2) + " rad";
    },
  },
  {
    name: "color_sensor", type: "turtlesim/msg/Color",
    label: "color sensor", show: trace(byId("sensor-summary"), byId("sensor-details")),
    summarize({ r, g, b }) {
      byId("color").textContent = [r, g, b].join(", ");
      return "Red " + r + ", green " + g + ", blue " + b;
    },
  },
];

function velocitySummary({ linear, angular }) {
  return "forward " + linear.x + ", strafe " + linear.y + ", turn " + angular.z;
}

function addRecord(kind, endpoint, limit) {
  const record = document.createElement("article");
  const title = document.createElement("h4");
  const name = document.createElement("code");
  name.textContent = endpoint;
  title.append(name);
  record.append(title);
  const list = byId(kind + "-records");
  list.prepend(record);
  while (list.childElementCount > limit) list.lastElementChild.remove();
  byId(kind + "-empty").hidden = true;
  return record;
}

function addStage(record, label) {
  const summary = document.createElement("p");
  const details = document.createElement("details");
  details.hidden = true;
  const toggle = document.createElement("summary");
  toggle.textContent = label + " JSON";
  details.append(toggle, document.createElement("pre"));
  record.append(summary, details);
  return trace(summary, details);
}

function selectTab(tab, focus = false) {
  const next = tab.getAttribute("aria-controls");
  if (next !== activeTab) stopMotion();
  activeTab = next;
  for (const button of tabs) {
    const selected = button === tab;
    button.setAttribute("aria-selected", String(selected));
    button.tabIndex = selected ? 0 : -1;
    byId(button.getAttribute("aria-controls")).hidden = !selected;
  }
  if (focus) tab.focus();
}

tabs.forEach((tab, index) => {
  tab.addEventListener("click", () => selectTab(tab));
  tab.addEventListener("keydown", (event) => {
    const next = {
      ArrowLeft: (index + tabs.length - 1) % tabs.length,
      ArrowRight: (index + 1) % tabs.length,
      Home: 0,
      End: tabs.length - 1,
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    event.stopPropagation();
    selectTab(tabs[next], true);
  });
});

function bindChoicePanels(list, attribute) {
  const panels = document.querySelectorAll("[" + attribute + "]");
  const update = () => {
    const selected = list.querySelector("input:checked").value;
    for (const panel of panels) panel.hidden = panel.getAttribute(attribute) !== selected;
  };
  list.addEventListener("change", update);
  update();
}

bindChoicePanels(byId("service-list"), "data-service-form");
bindChoicePanels(byId("topic-list"), "data-topic-view");

function report(message, error = false) {
  activity.textContent = message;
  activity.classList.toggle("error", error);
}

function showConnection(message, connected) {
  connection.textContent = message;
  connection.classList.toggle("connected", connected);
  picker.disabled = !connected;
  actionList.disabled = !connected;
  byId("service-tools").disabled = !connected;
  parameterList.disabled = !connected || !parameterValues.size;
  parameterTools.disabled = parameterList.disabled;
  updateTurtleControls();
}

function updateTurtleControls() {
  const disabled = picker.disabled || !selectedTurtle;
  driveTools.disabled = disabled;
  actionTools.disabled = picker.disabled || (!selectedTurtle && !rotation);
  byId("rotate").querySelector('button:not([type="button"])').disabled = disabled || !!rotation;
  const activeAction = byId("active-action");
  activeAction.hidden = !rotation;
  activeAction.textContent = rotation ? "Active goal on " + rotation.action : "";
  for (const control of document.querySelectorAll("[data-needs-turtle] input, [data-needs-turtle] button")) {
    control.disabled = !selectedTurtle;
  }
}

function watchScreen() {
  const viewer = new RFB(byId("screen"), "ws://" + window.location.host + "/websockify");
  viewer.viewOnly = true;
  viewer.scaleViewport = true;
  viewer.addEventListener("disconnect", () => setTimeout(watchScreen, 1500));
}

function send(message) {
  if (ws?.readyState !== WebSocket.OPEN) {
    throw new Error("The simulator’s rosbridge is disconnected.");
  }
  ws.send(JSON.stringify(message));
}

function changeSelection(name) {
  stopMotion();
  followTopics.forEach(({ topic, id }) => send({ op: "unsubscribe", topic, id }));
  selectedTurtle = name;
  for (const radio of actionList.querySelectorAll("input")) radio.checked = radio.value === name;
  for (const label of document.querySelectorAll("[data-interface]")) {
    label.textContent = name ? "/" + name + "/" + label.dataset.interface : "Select a turtle";
  }
  commandCount = 0;
  lastMovement = undefined;
  showCommand("Drive to publish a velocity command.");
  for (const { label, show } of topicStreams) {
    show(name ? "Waiting for a " + label + " message…" : "Select a turtle to see live messages.");
  }
  followTopics = name ? topicStreams.map((stream) => ({
    ...stream, topic: "/" + name + "/" + stream.name, id: "watch-" + ++nextId, count: 0,
  })) : [];
  for (const { topic, type, id } of followTopics) {
    send({ op: "subscribe", topic, type, id, throttle_rate: 100, queue_length: 1 });
  }
  for (const id of [...Object.values(poseFields), "color"]) byId(id).textContent = "—";
  updateTurtleControls();
}

function updateTurtles(names, preferred = selectedTurtle) {
  const choices = [...new Set(names)].sort();
  turtleSelect.replaceChildren(...choices.map((name) => new Option(name, name)));
  if (!choices.length) turtleSelect.add(new Option("No turtles", ""));
  turtleSelect.value = choices.includes(preferred) ? preferred : (choices[0] ?? "");
  updateActionList(choices);
  if (turtleSelect.value !== selectedTurtle) changeSelection(turtleSelect.value);
}

function updateActionList(names) {
  actionList.replaceChildren(actionList.querySelector("legend"));
  if (!names.length) {
    const empty = document.createElement("p");
    empty.className = "exercise";
    empty.textContent = "Spawn a turtle to see its rotation action.";
    actionList.append(empty);
  }
  for (const name of names) {
    const option = document.createElement("label");
    const radio = document.createElement("input");
    radio.type = "radio";
    radio.name = "rotation-action";
    radio.value = name;
    radio.checked = name === turtleSelect.value;
    const title = document.createElement("span");
    const endpoint = document.createElement("code");
    endpoint.textContent = "/" + name + "/rotate_absolute";
    const type = document.createElement("code");
    type.className = "topic-meta";
    type.textContent = rotationType;
    title.append(endpoint, type);
    option.append(radio, title);
    actionList.append(option);
  }
}

function settleService(id, error, values, packet) {
  const request = pendingServices.get(id);
  if (!request) return false;
  clearTimeout(request.timer);
  pendingServices.delete(id);
  request.showResult?.(error ? "Response error: " + error.message : "Response received.", packet);
  if (error) request.reject(error);
  else request.resolve(values);
  return true;
}

function call(service, args = {}, show = true) {
  const id = "service-" + ++nextId;
  const packet = { op: "call_service", id, service, args };
  return new Promise((resolve, reject) => {
    let showRequest;
    let showResult;
    if (show) {
      const record = addRecord(show === "parameter" ? "parameter" : "service", service, 5);
      showRequest = addStage(record, "Request");
      showResult = addStage(record, "Response");
      showResult("Waiting for a response…");
    }
    const timer = setTimeout(() => {
      settleService(id, new Error("No response from " + service + "."));
    }, 7000);
    pendingServices.set(id, { timer, resolve, reject, showResult });
    try {
      send(packet);
      showRequest?.("Request sent.", packet);
    } catch (error) {
      showRequest?.("Request could not be sent.");
      settleService(id, error);
    }
  });
}

async function refreshTurtles(show = true) {
  const { topics, types } = await call("/rosapi/topics", {}, show);
  const names = topics.flatMap((topic, index) => {
    const match = topic.match(/^\/([A-Za-z_][A-Za-z0-9_]*)\/pose$/);
    return match && types[index] === "turtlesim/msg/Pose" ? [match[1]] : [];
  });
  updateTurtles(names);
}

function rgb(hex) {
  return [1, 3, 5].map((offset) => Number.parseInt(hex.slice(offset, offset + 2), 16));
}

function setHolonomicDisplay(enabled) {
  settings.elements.holonomic.checked = enabled;
  byId("strafe-left").disabled = !enabled;
  byId("strafe-right").disabled = !enabled;
  byId("strafe-hint").hidden = enabled;
}

async function readSettings() {
  const { result } = await call("/turtlesim/list_parameters", {}, false);
  const names = [...result.names].sort((a, b) =>
    Number(Object.hasOwn(parameterDescriptions, b)) - Number(Object.hasOwn(parameterDescriptions, a)));
  const { values } = await call("/turtlesim/get_parameters", { names }, false);
  parameterValues.clear();
  names.forEach((name, index) => parameterValues.set(name, values[index]));
  renderParameters(names);
  syncSettings();
  parameterList.disabled = false;
  parameterTools.disabled = false;
}

function renderParameters(names) {
  const previous = parameterList.querySelector("input:checked")?.value;
  const selected = names.includes(previous) ? previous : names.includes("background_r") ? "background_r" : names[0];
  parameterList.replaceChildren(parameterList.querySelector("legend"));
  for (const [label, editable] of [["Simulator", true], ["ROS runtime", false]]) {
    const group = document.createElement("div");
    const heading = document.createElement("h3");
    heading.textContent = label;
    group.append(heading);
    for (const name of names.filter((name) => Object.hasOwn(parameterDescriptions, name) === editable)) {
      const option = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "parameter";
      radio.value = name;
      radio.checked = name === selected;
      const title = document.createElement("span");
      const key = document.createElement("code");
      key.textContent = name;
      const current = document.createElement("span");
      current.className = "topic-meta";
      current.textContent = describeParameter(parameterValues.get(name));
      title.append(key, current);
      option.append(radio, title);
      group.append(option);
    }
    if (group.childElementCount > 1) parameterList.append(group);
  }
  selectParameter();
}

function describeParameter(value) {
  const [type, field] = parameterTypes[value?.type] ?? parameterTypes[0];
  return field ? type + " · " + JSON.stringify(value[field]) : type;
}

function selectParameter() {
  const name = parameterList.querySelector("input:checked")?.value;
  const value = parameterValues.get(name);
  const editable = Object.hasOwn(parameterDescriptions, name) && (value?.type === 1 || value?.type === 2);
  byId("parameter-name").textContent = name ?? "Select a parameter";
  byId("parameter-current").textContent = value ? "Current value: " + describeParameter(value) : "";
  byId("parameter-description").textContent = editable ? parameterDescriptions[name] :
    name ? "Read-only in this lab. ROS uses this setting to configure the node runtime." : "";
  parameterEdit.hidden = !editable;
  const boolean = value?.type === 1;
  byId("parameter-number-label").hidden = boolean;
  byId("parameter-bool-label").hidden = !boolean;
  parameterEdit.elements.integer.disabled = boolean;
  parameterEdit.elements.integer.value = value?.integer_value ?? 0;
  parameterEdit.elements.boolean.checked = value?.bool_value ?? false;
}

function syncSettings() {
  const channels = backgroundParameters.map((name) => parameterValues.get(name)?.integer_value);
  if (channels.every(Number.isInteger)) {
    settings.elements.color.value = "#" + channels.map((channel) => channel.toString(16).padStart(2, "0")).join("");
  }
  const holonomic = parameterValues.get("holonomic");
  if (holonomic) setHolonomicDisplay(holonomic.bool_value);
}

function updateParameterValues(changes) {
  const checked = parameterList.querySelector("input:checked");
  for (const { name, value } of changes) {
    parameterValues.set(name, value);
    const radio = [...parameterList.querySelectorAll("input")].find((item) => item.value === name);
    if (radio) radio.parentElement.querySelector(".topic-meta").textContent = describeParameter(value);
    if (checked?.value === name) byId("parameter-current").textContent = "Current value: " + describeParameter(value);
  }
  syncSettings();
}

function serviceError({ result, service, values }) {
  if (result === false) {
    return new Error(typeof values === "string" ? values : service + " failed.");
  }
  if (values?.result?.successful === false) {
    return new Error(values.result.reason || service + " rejected the request.");
  }
  // Turtlesim can return an empty name when a requested name is already in use.
  if (service === "/spawn" && !values?.name) {
    return new Error("Turtlesim did not spawn a turtle. Try a unique name.");
  }
  return null;
}

function receive({ data }) {
  const packet = JSON.parse(data);
  if (packet.op === "publish") {
    if (packet.topic === "/parameter_events" && packet.msg.node === "/turtlesim") {
      updateParameterValues([...packet.msg.new_parameters, ...packet.msg.changed_parameters]);
    }
    const stream = followTopics.find(({ topic }) => topic === packet.topic);
    if (stream) stream.show("Received " + ++stream.count + " · " + stream.summarize(packet.msg) + ".", packet);
  }
  if (packet.op === "service_response") {
    settleService(packet.id, serviceError(packet), packet.values, packet);
  }
  if (packet.op === "action_feedback" && rotation && packet.id === rotation.id) {
    rotation.showFeedback("Feedback " + ++rotation.count + " · " + packet.values.remaining.toFixed(2) +
      " rad remaining.", packet);
  }
  if (packet.op === "action_result" && rotation && packet.id === rotation.id) {
    const state = { 4: "Rotation complete.", 5: "Rotation cancelled.", 6: "Rotation aborted." };
    finishRotation(state[packet.status] ?? (packet.result ? "Rotation complete." : "Rotation failed."), packet);
  }
  if (packet.op === "status" && packet.level === "error") {
    if (rotation && packet.id === rotation.id) {
      finishRotation("Action error: " + packet.msg, packet);
    } else if (!settleService(packet.id, new Error(packet.msg), undefined, packet)) {
      report(packet.msg, true);
    }
  }
}

function connect() {
  showConnection("Connecting to local rosbridge…", false);
  ws = new WebSocket(bridgeUrl);
  ws.addEventListener("message", receive);
  ws.addEventListener("open", () => {
    showConnection("Connected to local rosbridge", true);
    run(async () => {
      updateTurtles(["turtle1"]);
      send({ op: "subscribe", id: "turtlesim-parameters", topic: "/parameter_events", type: "rcl_interfaces/msg/ParameterEvent" });
      await readSettings();
    });
    run(() => refreshTurtles(false));
  });
  ws.addEventListener("close", () => {
    if (driving) clearInterval(driving.timer);
    driving = undefined;
    if (rotation) finishRotation("Disconnected before ROS reported a result.");
    for (const id of pendingServices.keys()) settleService(id, new Error("Rosbridge disconnected."));
    advertised.clear();
    followTopics = [];
    selectedTurtle = "";
    for (const { show } of topicStreams) show("Disconnected. Waiting for fresh messages.");
    showConnection("Rosbridge disconnected. Reconnecting…", false);
    setTimeout(connect, 1500);
  });
}

function turtlePath(suffix) {
  if (!selectedTurtle) throw new Error("Select or spawn a turtle first.");
  return "/" + selectedTurtle + "/" + suffix;
}

function publishMotion(topic, [forward, strafe, turn]) {
  if (!advertised.has(topic)) {
    send({ op: "advertise", topic, type: "geometry_msgs/msg/Twist" });
    advertised.add(topic);
  }
  const packet = { op: "publish", topic, msg: {
    linear: { x: forward, y: strafe, z: 0 },
    angular: { x: 0, y: 0, z: turn },
  } };
  send(packet);
  const moving = !!(forward || strafe || turn);
  if (moving) lastMovement = packet;
  const previous = lastMovement?.msg;
  showCommand("Sent " + ++commandCount + " · " + (moving ? velocitySummary(packet.msg) : "zero velocity (stop)") +
    (!moving && previous ? " · Previous movement: " + velocitySummary(previous) + "." : "."),
  !moving && lastMovement ? { previousMovement: lastMovement, latest: packet } : packet);
}

function startMotion(input, vector) {
  if (activeTab !== "topics" || driveTools.disabled || driving?.input === input) return;
  stopMotion();
  const topic = turtlePath("cmd_vel");
  publishMotion(topic, vector);
  const timer = setInterval(() => {
    if (ws.readyState === WebSocket.OPEN) publishMotion(topic, vector);
  }, 100);
  driving = { input, topic, timer };
}

function stopMotion(input) {
  if (!driving || (input !== undefined && driving.input !== input)) return;
  const { topic, timer } = driving;
  clearInterval(timer);
  driving = undefined;
  if (ws?.readyState === WebSocket.OPEN) publishMotion(topic, [0, 0, 0]);
}

function finishRotation(message, packet) {
  clearTimeout(rotation.timer);
  rotation.showResult(message, packet);
  rotation = undefined;
  cancelButton.disabled = true;
  updateTurtleControls();
}

function cancelRotation() {
  if (rotation && !rotation.cancelling) {
    const { id, action } = rotation;
    const packet = { op: "cancel_action_goal", id, action };
    send(packet);
    rotation.cancelling = true;
    cancelButton.disabled = true;
    rotation.showCancel("Cancellation requested.", packet);
    rotation.showResult("Waiting for ROS to report the outcome.");
  }
}

async function run(operation) {
  try {
    await operation();
  } catch (error) {
    report(error.message, true);
  }
}

function onButton(id, callback) {
  byId(id).addEventListener("click", () => run(callback));
}

function onForm(id, callback) {
  byId(id).addEventListener("submit", (event) => {
    event.preventDefault();
    run(() => callback(event.currentTarget.elements));
  });
}

turtleSelect.addEventListener("change", () => run(() => changeSelection(turtleSelect.value)));
actionList.addEventListener("change", (event) => run(() => {
  turtleSelect.value = event.target.value;
  changeSelection(turtleSelect.value);
}));
onButton("refresh", refreshTurtles);
onButton("stop", () => {
  stopMotion();
  if (rotation) cancelRotation();
  else publishMotion(turtlePath("cmd_vel"), [0, 0, 0]);
});
onButton("cancel", cancelRotation);

for (const button of document.querySelectorAll("[data-motion]")) {
  const vector = button.dataset.motion.split(",").map(Number);
  button.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) return;
    button.setPointerCapture(event.pointerId);
    run(() => startMotion(event.pointerId, vector));
  });
  for (const eventName of ["pointerup", "pointercancel", "lostpointercapture"]) {
    button.addEventListener(eventName, (event) => stopMotion(event.pointerId));
  }
  button.addEventListener("click", (event) => {
    if (event.detail !== 0) return;
    run(() => {
      startMotion(button, vector);
      setTimeout(() => stopMotion(button), 220);
    });
  });
}

document.addEventListener("keydown", (event) => {
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  const vector = keyboardMoves[key];
  if (!vector || activeTab !== "topics" || driveTools.disabled ||
      (vector[1] && byId("strafe-left").disabled) ||
      event.altKey || event.ctrlKey || event.metaKey ||
      event.target.closest("input, select, textarea, [contenteditable], .topic-message-body")) return;
  event.preventDefault();
  if (!event.repeat) run(() => startMotion(event.key, vector));
});
document.addEventListener("keyup", (event) => stopMotion(event.key));
window.addEventListener("blur", () => stopMotion());
document.addEventListener("visibilitychange", () => {
  if (document.hidden) stopMotion();
});

onForm("absolute", async ({ x, y, theta }) => {
  await call(turtlePath("teleport_absolute"), { x: x.valueAsNumber, y: y.valueAsNumber, theta: theta.valueAsNumber });
  report("Turtle teleported to the absolute pose.");
});
onForm("relative", async ({ linear, angular }) => {
  await call(turtlePath("teleport_relative"), { linear: linear.valueAsNumber, angular: angular.valueAsNumber });
  report("Relative teleport applied.");
});
onForm("rotate", ({ theta }) => {
  if (rotation) throw new Error("Cancel or finish the active rotation first.");
  stopMotion();
  const id = "rotate-" + ++nextId;
  const action = turtlePath("rotate_absolute");
  const packet = { op: "send_action_goal", id, action, action_type: rotationType,
    args: { theta: theta.valueAsNumber }, feedback: true };
  send(packet);
  const record = addRecord("action", action, 3);
  addStage(record, "Goal")("Goal sent · " + theta.valueAsNumber + " rad.", packet);
  const showFeedback = addStage(record, "Feedback");
  const showCancel = addStage(record, "Cancellation");
  const showResult = addStage(record, "Result");
  showFeedback("Waiting for feedback…");
  showResult("Waiting for a result…");
  const timer = setTimeout(() => {
    finishRotation("No rotation result received within 15 seconds.");
  }, 15000);
  rotation = { id, action, timer, count: 0, showFeedback, showCancel, showResult };
  cancelButton.disabled = false;
  updateTurtleControls();
});

onForm("spawn", async ({ name, x, y, theta }) => {
  const result = await call("/spawn", { name: name.value, x: x.valueAsNumber, y: y.valueAsNumber, theta: theta.valueAsNumber });
  updateTurtles([...turtleSelect.options].map((option) => option.value).filter(Boolean).concat(result.name), result.name);
  report("Spawned " + result.name + ".");
});
onButton("kill", async () => {
  const name = selectedTurtle;
  stopMotion();
  await call("/kill", { name });
  advertised.delete("/" + name + "/cmd_vel");
  updateTurtles([...turtleSelect.options].map((option) => option.value).filter((value) => value !== name));
  report("Removed " + name + ".");
});
onButton("clear", async () => {
  await call("/clear");
  report("Trails cleared.");
});
onButton("reset", async () => {
  stopMotion();
  await call("/reset");
  changeSelection("");
  updateTurtles(["turtle1"]);
  report("World reset.");
});
onForm("pen", async ({ color, width, enabled }) => {
  const [r, g, b] = rgb(color.value);
  await call(turtlePath("set_pen"), { r, g, b, width: width.valueAsNumber, off: enabled.checked ? 0 : 1 });
  report("Pen updated.");
});
onForm("settings", async ({ color, holonomic }) => {
  const parameters = backgroundParameters.map((name, index) => ({
    name, value: { type: 2, integer_value: rgb(color.value)[index] },
  }));
  parameters.push({ name: "holonomic", value: { type: 1, bool_value: holonomic.checked } });
  await call("/turtlesim/set_parameters_atomically", { parameters });
  updateParameterValues(parameters);
  report("World settings updated.");
});

parameterList.addEventListener("change", selectParameter);
onForm("parameter-edit", async ({ integer, boolean }) => {
  const name = parameterList.querySelector("input:checked")?.value;
  const current = parameterValues.get(name);
  if (!Object.hasOwn(parameterDescriptions, name) || !current) return;
  const value = current.type === 1 ? { type: 1, bool_value: boolean.checked } :
    { type: 2, integer_value: integer.valueAsNumber };
  await call("/turtlesim/set_parameters_atomically", { parameters: [{ name, value }] }, "parameter");
  const { values } = await call("/turtlesim/get_parameters", { names: [name] }, false);
  updateParameterValues([{ name, value: values[0] }]);
  report(name + " updated.");
});

watchScreen();
connect();

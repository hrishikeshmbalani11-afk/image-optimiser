const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const statusEl = document.getElementById("status");
const beforeImage = document.getElementById("before-image");
const beforePlaceholder = document.getElementById("before-placeholder");
const optimizeBtn = document.getElementById("optimize-btn");
const afterImage = document.getElementById("after-image");
const afterPlaceholder = document.getElementById("after-placeholder");
const downloadLink = document.getElementById("download-link");
const resultMeta = document.getElementById("result-meta");
const presetInput = document.getElementById("preset");
const qualityControl = document.getElementById("quality-control");
const qualityInput = document.getElementById("quality");
const qualityValue = document.getElementById("quality-value");
const resizeInput = document.getElementById("resize-percent");
const resizeValue = document.getElementById("resize-value");
const outputFormatInput = document.getElementById("output-format");
const sharpnessBalanceInput = document.getElementById("sharpness-balance");
const sharpnessBalanceValue = document.getElementById("sharpness-balance-value");
const contrastInput = document.getElementById("contrast");
const contrastValue = document.getElementById("contrast-value");
const brightnessInput = document.getElementById("brightness");
const brightnessValue = document.getElementById("brightness-value");
const stripMetadataInput = document.getElementById("strip-metadata");
const autoOrientInput = document.getElementById("auto-orient");
const paramsPreview = document.getElementById("params-preview");

let selectedFile = null;
let beforeObjectUrl = "";

const setStatus = (message, isError = false) => {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
};

const presetBounds = {
  speed: [30, 50],
  balanced: [50, 75],
  max_quality: [80, 95],
  custom_quality: [1, 95],
};
const presetDefaults = {
  speed: 40,
  balanced: 65,
  max_quality: 92,
  custom_quality: 85,
};

const getEffectiveQuality = () => {
  const requestedQuality = Number(qualityInput.value);
  const [minQ, maxQ] = presetBounds[presetInput.value];
  return Math.min(Math.max(requestedQuality, minQ), maxQ);
};

const updateParamsPreview = () => {
  const isCustomQuality = presetInput.value === "custom_quality";
  if (isCustomQuality) {
    qualityControl.hidden = false;
    qualityControl.style.display = "flex";
    qualityInput.disabled = false;
  } else {
    qualityControl.hidden = true;
    qualityControl.style.display = "none";
    qualityInput.disabled = true;
  }
  if (!isCustomQuality) {
    qualityInput.value = String(presetDefaults[presetInput.value]);
  }
  qualityValue.textContent = qualityInput.value;
  resizeValue.textContent = `${resizeInput.value}%`;
  resizeValue.textContent = `${resizeInput.value}%`;
  sharpnessBalanceValue.textContent = Number(sharpnessBalanceInput.value).toFixed(1);
  contrastValue.textContent = Number(contrastInput.value).toFixed(1);
  brightnessValue.textContent = Number(brightnessInput.value).toFixed(1);
  const [minQ, maxQ] = presetBounds[presetInput.value];
  const effectiveQuality = getEffectiveQuality();
  const qualityNote = isCustomQuality
    ? "Direct quality control enabled."
    : `Preset-managed quality (${minQ}-${maxQ}).`;
  paramsPreview.textContent =
    `Preset: ${presetInput.value}. ` +
    `${isCustomQuality ? `Requested quality: ${qualityInput.value}.` : `Preset quality target: ${qualityInput.value}.`} ` +
    `Effective quality on optimize: ${effectiveQuality}. ${qualityNote} ` +
    `Resize: ${resizeInput.value}%. Output: ${outputFormatInput.value}. ` +
    `Blur <-> Sharpen: ${Number(sharpnessBalanceInput.value).toFixed(1)} (negative = blur, positive = sharpen). ` +
    `Contrast: ${Number(contrastInput.value).toFixed(1)}, Brightness: ${Number(brightnessInput.value).toFixed(1)}. ` +
    `Strip metadata: ${stripMetadataInput.checked ? "yes" : "no"}. ` +
    `Auto-orient: ${autoOrientInput.checked ? "yes" : "no"}.`;
};

const setSelectedFile = (file) => {
  const validTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!validTypes.includes(file.type)) {
    setStatus("Only JPEG, PNG, and WebP are supported.", true);
    return;
  }

  selectedFile = file;
  const mimeToFormat = { "image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP" };
  outputFormatInput.value = mimeToFormat[file.type] || "JPEG";
  if (beforeObjectUrl) {
    URL.revokeObjectURL(beforeObjectUrl);
  }
  beforeObjectUrl = URL.createObjectURL(file);
  beforeImage.src = beforeObjectUrl;
  beforeImage.style.display = "block";
  beforePlaceholder.style.display = "none";
  optimizeBtn.disabled = false;
  afterImage.style.display = "none";
  afterPlaceholder.style.display = "flex";
  downloadLink.hidden = true;
  resultMeta.textContent = "";
  setStatus("Image selected. Click Optimize Image.");
};

const optimizeImage = async () => {
  if (!selectedFile) {
    setStatus("Please upload an image first.", true);
    return;
  }

  const formData = new FormData();
  formData.append("image", selectedFile);
  formData.append("preset", presetInput.value);
  formData.append("quality", qualityInput.value);
  formData.append("resize_percent", resizeInput.value);
  formData.append("output_format", outputFormatInput.value);
  formData.append("sharpness_balance", sharpnessBalanceInput.value);
  formData.append("contrast", contrastInput.value);
  formData.append("brightness", brightnessInput.value);
  formData.append("strip_metadata", String(stripMetadataInput.checked));
  formData.append("auto_orient", String(autoOrientInput.checked));

  optimizeBtn.disabled = true;
  setStatus("Optimizing image...");
  try {
    const response = await fetch("/optimize", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      setStatus(data.error || "Optimization failed.", true);
      return;
    }

    afterImage.src = data.after_data_url;
    afterImage.style.display = "block";
    afterPlaceholder.style.display = "none";
    downloadLink.href = data.after_data_url;
    downloadLink.download = data.after_filename;
    downloadLink.hidden = false;
    const changedSummaries = [];
    if (data.after_size < data.before_size) {
      changedSummaries.push(`Saved ${Math.abs(data.size_change_percent)}% (${data.before_size} B -> ${data.after_size} B)`);
    } else if (data.after_size > data.before_size) {
      changedSummaries.push(`Increased by ${Math.abs(data.size_change_percent)}% (${data.before_size} B -> ${data.after_size} B)`);
    }
    if (data.before_width !== data.after_width || data.before_height !== data.after_height) {
      changedSummaries.push(`Dimensions: ${data.before_width}x${data.before_height} -> ${data.after_width}x${data.after_height}`);
    }
    if (data.input_format !== data.output_format) {
      changedSummaries.push(`Format: ${data.input_format} -> ${data.output_format}`);
    }
    if (Math.abs(Number(data.brightness) - 1.0) > 0.001) {
      changedSummaries.push(`Brightness: ${Number(data.brightness).toFixed(1)}`);
    }
    if (Math.abs(Number(data.contrast) - 1.0) > 0.001) {
      changedSummaries.push(`Contrast: ${Number(data.contrast).toFixed(1)}`);
    }
    if (Math.abs(Number(data.sharpness_balance)) > 0.001) {
      if (Number(data.sharpness_balance) > 0) {
        changedSummaries.push(`Sharpen: ${Number(data.sharpness_balance).toFixed(1)}`);
      } else {
        changedSummaries.push(`Blur: ${Math.abs(Number(data.sharpness_balance)).toFixed(1)}`);
      }
    }

    resultMeta.textContent = changedSummaries.length > 0
      ? `${changedSummaries.join(". ")}.`
      : "No changes from current defaults.";
    setStatus("Optimization complete.");
  } catch (_err) {
    setStatus("Optimization failed. Please try again.", true);
  } finally {
    optimizeBtn.disabled = false;
  }
};

dropzone.addEventListener("click", () => fileInput.click());

["dragenter", "dragover"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.add("active");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => {
    event.preventDefault();
    dropzone.classList.remove("active");
  });
});

dropzone.addEventListener("drop", (event) => {
  const file = event.dataTransfer.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  if (file) {
    setSelectedFile(file);
  }
});

optimizeBtn.addEventListener("click", optimizeImage);
[presetInput, qualityInput, resizeInput, outputFormatInput, sharpnessBalanceInput, contrastInput, brightnessInput, stripMetadataInput, autoOrientInput].forEach((input) => {
  input.addEventListener("input", updateParamsPreview);
  input.addEventListener("change", updateParamsPreview);
});
updateParamsPreview();

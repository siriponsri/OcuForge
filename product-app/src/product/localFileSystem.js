export class LocalFileSystemBridge {
  constructor() {
    this.outputDirectoryHandle = null;
  }

  get supportsDirectoryPicker() {
    return typeof window !== "undefined" && typeof window.showDirectoryPicker === "function";
  }

  filesFromInput(event) {
    return [...(event.target.files || [])];
  }

  async chooseOutputDirectory() {
    if (!this.supportsDirectoryPicker) return null;
    this.outputDirectoryHandle = await window.showDirectoryPicker({ mode: "readwrite" });
    return this.outputDirectoryHandle;
  }

  describeInput(files) {
    if (!files.length) return "No folder selected";
    const relative = files.find((file) => file.webkitRelativePath)?.webkitRelativePath;
    return relative ? relative.split("/")[0] : `${files.length} local files`;
  }
}

export const localFileSystemBridge = new LocalFileSystemBridge();

/**
 * DevIntel VS Code Extension — Main entry point.
 *
 * Registers:
 *  - Sidebar webview (DevIntel AI Chat)
 *  - Command: DevIntel: Ask AI         — focuses the sidebar chat
 *  - Command: DevIntel: Review File    — semantic search + review of current file
 *  - Command: DevIntel: Set API Token  — stores JWT in SecretStorage
 *  - Command: DevIntel: Set API URL    — persists base URL in workspace settings
 */

import * as vscode from "vscode";
import { DevIntelSidebarProvider } from "./sidebar";
import { DevIntelAuth } from "./auth";

export function activate(context: vscode.ExtensionContext) {
    const auth = new DevIntelAuth(context.secrets);
    const sidebarProvider = new DevIntelSidebarProvider(context.extensionUri, auth);

    // Register sidebar view
    context.subscriptions.push(
        vscode.window.registerWebviewViewProvider("devintel.sidebar", sidebarProvider, {
            webviewOptions: { retainContextWhenHidden: true },
        })
    );

    // Command: Ask AI — focuses the sidebar
    context.subscriptions.push(
        vscode.commands.registerCommand("devintel.ask", async () => {
            await vscode.commands.executeCommand("devintel.sidebar.focus");
        })
    );

    // Command: Review Current File
    context.subscriptions.push(
        vscode.commands.registerCommand("devintel.reviewFile", async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage("DevIntel: No active file to review.");
                return;
            }

            const filePath = editor.document.fileName;
            const fileContent = editor.document.getText();
            const language = editor.document.languageId;

            await sidebarProvider.triggerFileReview(filePath, fileContent, language);
            await vscode.commands.executeCommand("devintel.sidebar.focus");
        })
    );

    // Command: Set API Token
    context.subscriptions.push(
        vscode.commands.registerCommand("devintel.setApiToken", async () => {
            const token = await vscode.window.showInputBox({
                prompt: "Paste your DevIntel API token (JWT access token from app settings)",
                password: true,
                placeHolder: "eyJ...",
                validateInput: (v) => (v.length > 10 ? null : "Token looks too short"),
            });
            if (token) {
                await auth.setToken(token);
                sidebarProvider.notifyAuthChanged();
                vscode.window.showInformationMessage("✅ DevIntel: API token saved securely.");
            }
        })
    );

    // Command: Set API URL
    context.subscriptions.push(
        vscode.commands.registerCommand("devintel.setApiUrl", async () => {
            const current = vscode.workspace
                .getConfiguration("devintel")
                .get<string>("apiBaseUrl", "http://localhost:8000");
            const url = await vscode.window.showInputBox({
                prompt: "DevIntel API base URL",
                value: current,
                validateInput: (v) =>
                    v.startsWith("http") ? null : "Must start with http:// or https://",
            });
            if (url) {
                await vscode.workspace
                    .getConfiguration("devintel")
                    .update("apiBaseUrl", url, vscode.ConfigurationTarget.Global);
                vscode.window.showInformationMessage(`DevIntel: API URL set to ${url}`);
            }
        })
    );

    vscode.window.showInformationMessage("🚀 DevIntel AI is ready.");
}

export function deactivate() { }

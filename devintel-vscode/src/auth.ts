/**
 * DevIntelAuth — Manages API token and base URL storage.
 * Token is stored in VS Code's SecretStorage (OS keychain / encrypted store).
 * Base URL is stored in extension settings (workspace-level config).
 */

import * as vscode from "vscode";

export class DevIntelAuth {
    private static readonly TOKEN_KEY = "devintel.apiToken";

    constructor(private readonly secrets: vscode.SecretStorage) { }

    async getToken(): Promise<string | undefined> {
        return this.secrets.get(DevIntelAuth.TOKEN_KEY);
    }

    async setToken(token: string): Promise<void> {
        await this.secrets.store(DevIntelAuth.TOKEN_KEY, token);
    }

    async clearToken(): Promise<void> {
        await this.secrets.delete(DevIntelAuth.TOKEN_KEY);
    }

    getApiBaseUrl(): string {
        return vscode.workspace
            .getConfiguration("devintel")
            .get<string>("apiBaseUrl", "http://localhost:8000");
    }

    /** Build Authorization headers for fetch calls */
    async buildHeaders(): Promise<Record<string, string>> {
        const token = await this.getToken();
        return {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        };
    }
}

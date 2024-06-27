import { App } from "../../app.js";
import { FallTask, Rejected } from "../../utils.js";
import { CodeMaoClient, LoggedData } from "../CodeMaoClient.js";
import { AuthProvider } from "../auth.js";


export type LoginInfo = {
    user_info: {
        id: number;
        nickname: string;
        avatar_url: string;
        fullname: string;
        sex: 0 | 1;
        birthday: number;
        qq: string;
        description: string;
    };
    auth: {
        token: string;
        email: string;
        phone_number: string;
        has_password: boolean;
        is_weak_password: number;
    }
}

export class Cred implements AuthProvider {
    static LOGIN_PID = "65edCTyg";
    constructor(protected app: App, protected client: CodeMaoClient) {}

    token: string = "";
    async login(): Promise<LoggedData | null> {
        const state: {
            username: string;
            password: string;
        } = {
            username: "",
            password: ""
        };

        const fall = new FallTask(this.app);
        fall.start(this.app.UI.color.blue("登录codemao.cn"));
        if (this.app.envConfig["USERNAME"] && this.app.envConfig["PASSWORD"]) {
            state.username = this.app.envConfig["USERNAME"];
            state.password = this.app.envConfig["PASSWORD"];
        } else {
            state.username = await fall.input("用户名:");
            state.password = await fall.password("密码:");
        }
        fall.step(this.app.UI.color.gray(""), 1);

        let res = await fall.waitForLoading<LoginInfo | Rejected>(async (resolve, reject) => {
            let r = await this._SendLoginRequest(state.username, state.password);
            if (!Rejected.isRejected(r)) {
                resolve("");
            } else {
                reject("登录失败！" + r.toString());
            }
            return r;
        }, "正在登录…")

        if (!Rejected.isRejected(res) && (res as LoginInfo).auth.token) {
            fall.end(this.app.UI.color.green("登录成功！"));

            this.token = (res as LoginInfo).auth.token;
            return {
                id: (res as LoginInfo).user_info.id.toString(),
                nickname: (res as LoginInfo).user_info.nickname,
                token: this.token
            }
        } else {
            fall.end(this.app.UI.color.red("登录失败！"));
            return null;
        }
    }
    async isLogin(): Promise<boolean> {
        return !!(await this.client.syncDetails(true));
    }
    private async _SendLoginRequest(username: string, password: string): Promise<LoginInfo | Rejected> {
        return this.client.request<LoginInfo>(CodeMaoClient.ENDPOINTS.login, {
            method: "POST",
            body: JSON.stringify({
                pid: Cred.LOGIN_PID,
                identity: username,
                password
            })
        })
    }
}
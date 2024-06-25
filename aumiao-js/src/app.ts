import type { UI } from "./types/ui.js";
import { Logger } from "./utils.js";

import * as commander from "commander";
import { EventEmitter } from "events";

import { CommandDefinition, ProgramDefinision } from "./types/command.js";
import { route } from "./app/router.js";

const { program, Option } = commander;

export type AppConfig = {
    debug: boolean;
    verbose: boolean;
}

export class App {
    static DefaultConfig: AppConfig = {
        debug: false,
        verbose: false,
    };
    static StaticConfig = {
        MAX_TRY: 128,
        ART_TEXT: `
 ________  ___  ___  _____ ______   ___  ________  ________                     ___  ________      
|\\   __  \\|\\  \\|\\  \\|\\   _ \\  _   \\|\\  \\|\\   __  \\|\\   __  \\                   |\\  \\|\\   ____\\     
\\ \\  \\|\\  \\ \\  \\\\\\  \\ \\  \\\\\\__\\ \\  \\ \\  \\ \\  \\|\\  \\ \\  \\|\\  \\  ____________    \\ \\  \\ \\  \\___|_    
 \\ \\   __  \\ \\  \\\\\\  \\ \\  \\\\|__| \\  \\ \\  \\ \\   __  \\ \\  \\\\\\  \\|\\____________\\__ \\ \\  \\ \\_____  \\   
  \\ \\  \\ \\  \\ \\  \\\\\\  \\ \\  \\    \\ \\  \\ \\  \\ \\  \\ \\  \\ \\  \\\\\\  \\|____________|\\  \\\\_\\  \\|____|\\  \\  
   \\ \\__\\ \\__\\ \\_______\\ \\__\\    \\ \\__\\ \\__\\ \\__\\ \\__\\ \\_______\\            \\ \\________\\____\\_\\  \\ 
    \\|__|\\|__|\\|_______|\\|__|     \\|__|\\|__|\\|__|\\|__|\\|_______|             \\|________|\\_________\\
                                                                                       \\|_________|`,
    };
    static EXIT_CODES = {
        SUCCESS: 0,
        ERROR: 1,
    };
    static EVENTS = {
        START: "start",
        STOP: "stop",
    };


    UI: typeof UI;
    config: AppConfig;
    Logger: Logger;
    events: EventEmitter = new EventEmitter();
    program: commander.Command;
    App: typeof App = App;
    commands: { [name: string]: commander.Command };

    get options() {
        return this.program.opts();
    }

    constructor({
        UIUtils,
        config,
    }: {
        UIUtils: typeof UI,
        config: Partial<AppConfig>,
    }) {
        this.UI = UIUtils;
        this.config = { ...this.App.DefaultConfig, ...config };

        this.program = program;
        this.Logger = new Logger(this);
        this.commands = {};
    }

    public start() {
        this.events.emit(App.EVENTS.START);
        this.Logger.verbose("Starting app...");
        this.program.parse(process.argv);
    }

    public registerProgram({ name, description, version }: ProgramDefinision) {
        this.program.name(name)
            .description(description)
            .version(version)
            .action(async () => {
                await route("index", this);
            });
        return this;
    }
    public registerCommand(command: CommandDefinition, parent = this.program, root: Record<string, any> = {}) {
        const cmd = new commander.Command(command.name)
            .description(command.description)
            .action(async () => {
                await this.runCommand(cmd, command);
            });
        command.options?.forEach(option => {
            cmd.option(option.flags, option.description, option.defaultValue);
        });
        parent.addCommand(cmd);
        root[command.name] = { ...command, command: cmd, children: {} };
        if (command.children) this.registerCommands(command.children, cmd, root[command.name].children);
        return this;
    }
    public registerCommands(commands: CommandDefinition[], parent = this.program, root: Record<string, any> = {}) {
        commands.forEach(command => {
            this.registerCommand(command, parent, root);
        });
        return this;
    }

    protected async runCommand(command: commander.Command, config: CommandDefinition) {
        try {
            await route(config.name, this);
        } catch (err) {
            this.Logger.error("Crashed while executing the command: " + config.name || command.name());
            this.Logger.error(err as any);
            this.exit(this.App.EXIT_CODES.ERROR);
        }
    }

    on(event: string, listener: (...args: any[]) => void) {
        this.events.on(event, listener);
    }
    emit(event: string, ...args: any[]) {
        this.events.emit(event, ...args);
    }

    exit(code: number) {
        process.exit(code);
    }
}


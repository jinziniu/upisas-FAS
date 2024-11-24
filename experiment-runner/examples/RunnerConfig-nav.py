from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
import requests
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from typing import Dict, Optional
from pathlib import Path
from os.path import dirname, realpath

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # Experiment configuration
    name: str = "crowdnav_test_experiment"
    results_output_path: Path = ROOT_DIR / 'experiments'
    operation_type: OperationType = OperationType.AUTO
    time_between_runs_in_ms: int = 1000

    def __init__(self):
        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.BEFORE_EXPERIMENT, self.before_experiment),
            (RunnerEvents.BEFORE_RUN, self.before_run),
            (RunnerEvents.START_RUN, self.start_run),
            (RunnerEvents.START_MEASUREMENT, self.start_measurement),
            (RunnerEvents.INTERACT, self.interact),
            (RunnerEvents.STOP_MEASUREMENT, self.stop_measurement),
            (RunnerEvents.STOP_RUN, self.stop_run),
            (RunnerEvents.POPULATE_RUN_DATA, self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT, self.after_experiment),
        ])
        self.run_table_model = None
        self.monitor_data = {}
        output.console_log("Custom config loaded")

    def create_run_table_model(self) -> RunTableModel:
        factor1 = FactorModel("router_type", ['default', 'custom'])
        factor2 = FactorModel("dynamic_config", [True, False])
        self.run_table_model = RunTableModel(
            factors=[factor1, factor2],
            exclude_variations=[
                {factor1: ['custom'], factor2: [False]}
            ],
            repetitions=3,
            data_columns=['avg_response_time', 'max_memory_usage']
        )
        return self.run_table_model

    def before_experiment(self) -> None:
        output.console_log("Setting up CrowdNav experiment...")

    def before_run(self) -> None:
        output.console_log("Preparing for a new run...")

    def start_run(self, context: RunnerContext) -> None:
        output.console_log("Starting a new CrowdNav simulation...")
        response = requests.put("http://localhost:8080/execute", json={
            "action": "start_simulation",
            "parameters": {
                "duration": 1000,
                "router": context.current_run["router_type"],
                "dynamic_config": context.current_run["dynamic_config"],
            }
        })
        if response.status_code != 200:
            raise RuntimeError(f"Failed to start simulation: {response.text}")

    def start_measurement(self, context: RunnerContext) -> None:
        output.console_log("Collecting monitoring data from CrowdNav...")
        response = requests.get("http://localhost:8080/monitor")
        if response.status_code == 200:
            self.monitor_data = response.json()
        else:
            raise RuntimeError(f"Failed to monitor simulation: {response.text}")

    def interact(self, context: RunnerContext) -> None:
        output.console_log("Interacting with CrowdNav...")

    def stop_measurement(self, context: RunnerContext) -> None:
        output.console_log("Stopping measurement...")

    def stop_run(self, context: RunnerContext) -> None:
        output.console_log("Run completed. Finalizing...")

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, str]]:
        output.console_log("Processing and storing measurement data...")
        avg_response_time = self.monitor_data.get("avg_response_time", 0)
        max_memory_usage = self.monitor_data.get("max_memory_usage", 0)
        return {
            "avg_response_time": str(avg_response_time),
            "max_memory_usage": str(max_memory_usage)
        }

    def after_experiment(self) -> None:
        output.console_log("Experiment finished. Cleaning up resources...")

    experiment_path: Path = None

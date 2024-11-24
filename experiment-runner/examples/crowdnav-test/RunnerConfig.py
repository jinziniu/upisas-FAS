from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output
import requests

from typing import Dict, List, Any, Optional
from pathlib import Path
from os.path import dirname, realpath


class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name: str = "crowdnav_test_experiment"

    """The path to store experiment results."""
    results_output_path: Path = ROOT_DIR / 'experiments'

    """Experiment operation type."""
    operation_type: OperationType = OperationType.AUTO

    """Time between runs in milliseconds."""
    time_between_runs_in_ms: int = 1000

    def __init__(self):
        """Executes immediately after program start, on config load."""
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
        self.run_table_model = None  # Initialized later
        self.monitor_data = {}  # Store monitoring data during the experiment
        output.console_log("Custom config loaded")

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model for CrowdNav."""
        factor1 = FactorModel("router_type", ['default', 'custom'])  # Router type
        factor2 = FactorModel("dynamic_config", [True, False])  # Dynamic configuration
        self.run_table_model = RunTableModel(
            factors=[factor1, factor2],
            exclude_variations=[
                {factor1: ['custom'], factor2: [False]},  # Exclude invalid combinations
            ],
            repetitions=3,  # Number of repetitions for each variation
            data_columns=['avg_response_time', 'max_memory_usage']
        )
        return self.run_table_model

    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment."""
        output.console_log("Setting up CrowdNav experiment...")
        # Optional: Validate if CrowdNav services are running

    def before_run(self) -> None:
        """Prepare for a new run."""
        output.console_log("Preparing for a new run...")

    def start_run(self, context: RunnerContext) -> None:
        """Start a new CrowdNav simulation."""
        output.console_log("Starting a new CrowdNav simulation...")
        response = requests.put("http://localhost:8080/execute", json={
            "action": "start_simulation",
            "parameters": {
                "duration": 1000,  # Simulation duration
                "router": context.current_run["router_type"],  # Router type
                "dynamic_config": context.current_run["dynamic_config"],  # Dynamic config
            }
        })
        if response.status_code != 200:
            raise RuntimeError(f"Failed to start simulation: {response.text}")

    def start_measurement(self, context: RunnerContext) -> None:
        """Collect monitoring data."""
        output.console_log("Collecting monitoring data from CrowdNav...")
        response = requests.get("http://localhost:8080/monitor")
        if response.status_code == 200:
            self.monitor_data = response.json()  # Save monitoring data
        else:
            raise RuntimeError(f"Failed to monitor simulation: {response.text}")

    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system."""
        output.console_log("Interacting with CrowdNav...")
        # Optional: Adjust settings via /adaptation_options API

    def stop_measurement(self, context: RunnerContext) -> None:
        """Stop the measurement."""
        output.console_log("Stopping measurement...")

    def stop_run(self, context: RunnerContext) -> None:
        """Stop the simulation run."""
        output.console_log("Run completed. Finalizing...")

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Process measurement data and store in run table."""
        output.console_log("Processing and storing measurement data...")
        avg_response_time = self.monitor_data.get("avg_response_time", 0)
        max_memory_usage = self.monitor_data.get("max_memory_usage", 0)
        return {
            "avg_response_time": avg_response_time,
            "max_memory_usage": max_memory_usage
        }

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment."""
        output.console_log("Experiment finished. Cleaning up resources...")
        # Optional: Generate reports or clean up services

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path: Path = None

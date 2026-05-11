from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from tradingagents.dataflows.utils import safe_ticker_component
from tradingagents.default_config import DEFAULT_CONFIG

from .config import Settings
from .models import AnalysisRequest, AnalysisResult, JobStatus, utc_now
from .store import JobStore


REPORT_FIELDS = (
    "market_report",
    "sentiment_report",
    "news_report",
    "fundamentals_report",
    "investment_plan",
    "trader_investment_plan",
    "final_trade_decision",
)


class AnalysisRunner:
    def __init__(self, store: JobStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings
        self.executor = ThreadPoolExecutor(max_workers=settings.max_workers)

    def submit(self, request: AnalysisRequest):
        job = self.store.create(request)
        self.executor.submit(self._run, job.id)
        return job

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def _build_config(self, request: AnalysisRequest) -> dict[str, Any]:
        config = DEFAULT_CONFIG.copy()
        config["results_dir"] = str(self.settings.results_dir)
        config["data_cache_dir"] = str(self.settings.cache_dir)
        config["memory_log_path"] = str(self.settings.memory_log_path)
        config["llm_provider"] = (
            request.llm_provider or self.settings.default_llm_provider
        )
        config["quick_think_llm"] = (
            request.quick_think_llm or self.settings.default_quick_model
        )
        config["deep_think_llm"] = (
            request.deep_think_llm or self.settings.default_deep_model
        )
        config["backend_url"] = (
            request.backend_url
            if request.backend_url is not None
            else self.settings.default_backend_url
        )
        config["max_debate_rounds"] = request.research_depth
        config["max_risk_discuss_rounds"] = request.research_depth
        config["checkpoint_enabled"] = request.checkpoint_enabled
        config["output_language"] = (
            request.output_language or self.settings.default_output_language
        )
        if request.data_vendors:
            config["data_vendors"] = request.data_vendors
        if request.tool_vendors:
            config["tool_vendors"] = request.tool_vendors
        return config

    def _extract_result(
        self,
        request: AnalysisRequest,
        final_state: dict[str, Any],
        decision: str,
    ) -> AnalysisResult:
        # Coerce report values to JSON-serializable strings.
        reports = {}
        for key in REPORT_FIELDS:
            value = final_state.get(key)
            if not value:
                continue
            # If value is an AIMessage-like object, extract its content
            try:
                from langchain_core.messages import AIMessage

                if isinstance(value, AIMessage):
                    reports[key] = getattr(value, "content", "")
                    continue
            except Exception:
                # langchain not available or import failed; fall back to attribute check
                pass

            # If it's a list (e.g., content blocks), join text pieces
            if isinstance(value, list):
                try:
                    parts = []
                    for item in value:
                        if hasattr(item, "content"):
                            parts.append(str(item.content))
                        else:
                            parts.append(str(item))
                    reports[key] = "\n".join(p for p in parts if p)
                    continue
                except Exception:
                    reports[key] = str(value)
                    continue

            # Fallback: stringify value
            reports[key] = str(value)
        safe_ticker = safe_ticker_component(request.ticker)
        state_log_path = (
            Path(self.settings.results_dir)
            / safe_ticker
            / "TradingAgentsStrategy_logs"
            / f"full_states_log_{request.trade_date.isoformat()}.json"
        )
        return AnalysisResult(
            decision=str(decision),
            final_trade_decision=str(final_state.get("final_trade_decision", "")),
            reports=reports,
            state_log_path=str(state_log_path),
        )

    def _run(self, job_id: str) -> None:
        job = self.store.get(job_id)
        if job is None:
            return

        self.store.update(
            job_id,
            status=JobStatus.running,
            started_at=utc_now(),
            error=None,
        )

        try:
            from tradingagents.graph.trading_graph import TradingAgentsGraph

            request = job.request
            graph = TradingAgentsGraph(
                selected_analysts=request.analysts,
                config=self._build_config(request),
                debug=False,
            )
            final_state, decision = graph.propagate(
                request.ticker,
                request.trade_date.isoformat(),
            )
            result = self._extract_result(request, final_state, decision)
            self.store.update(
                job_id,
                status=JobStatus.completed,
                completed_at=utc_now(),
                result=result,
            )
        except Exception as exc:
            self.store.update(
                job_id,
                status=JobStatus.failed,
                completed_at=utc_now(),
                error=str(exc),
            )


from __future__ import annotations

import logging
import time
from typing import Protocol

from app.pipeline.context import DocumentContext

logger = logging.getLogger(__name__)


class Step(Protocol):
    def run(self, context: DocumentContext) -> DocumentContext: ...


class Pipeline:
    def __init__(self, steps: list[Step]) -> None:
        self._steps = steps

    def run(self, context: DocumentContext) -> DocumentContext:
        for step in self._steps:
            step_name = type(step).__name__
            start = time.perf_counter()
            context = step.run(context)
            elapsed = time.perf_counter() - start
            logger.info("%s completed in %.2fs", step_name, elapsed)
        return context

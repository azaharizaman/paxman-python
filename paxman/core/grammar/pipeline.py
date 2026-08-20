"""PipelineGrammar base — fixed-order pipeline with optional stages."""

from __future__ import annotations

from typing import ClassVar, TypeVar

from paxman.core.domain import Grammar, RecognitionMatch
from paxman.core.grammar.stages import PipelineState, Stage

NotationT = TypeVar("NotationT")


class PipelineGrammar(Grammar[NotationT]):
    """Grammar that declares optional stages; recognize() walks them in fixed order."""

    # Placeholder semantics for the abstract base; concrete grammars override it
    # (Grammar.__init_subclass__ requires a non-empty semantics at class-def time).
    semantics: ClassVar[str] = "pipeline_grammar"

    # Stages — each is Optional[Stage]; None means "skip".
    pre: Stage[NotationT] | None = None
    regex: Stage[NotationT] | None = None
    lexicon: Stage[NotationT] | None = None
    composer: Stage[NotationT] | None = None
    post: Stage[NotationT] | None = None

    def recognize(self, text: str) -> list[RecognitionMatch[NotationT]]:
        state: PipelineState[NotationT] = PipelineState(
            text=text, matches=[], scratch={}
        )
        for stage in (
            self.pre,
            self.regex,
            self.lexicon,
            self.composer,
            self.post,
        ):
            if stage is not None:
                state = stage.run(state)
                # Pre short-circuit: if StandardPre emptied matches on whitespace-only
                # input, skip remaining stages — they would find nothing anyway.
                if (
                    self.pre is not None
                    and not state.text.strip()
                    and not state.matches
                ):
                    break
        return list(state.matches)

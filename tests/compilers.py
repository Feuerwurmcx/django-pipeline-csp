"""Compiler, der fuer die F1-Tests einen CompilerError provoziert."""

from pipeline.compilers import CompilerBase
from pipeline.exceptions import CompilerError


class FailingCompiler(CompilerBase):
    """Matcht `*.fail`-Dateien und bricht das Kompilieren immer ab."""

    output_extension = "js"

    def match_file(self, filename):
        return filename.endswith(".fail")

    def compile_file(self, infile, outfile, outdated=False, force=False):
        raise CompilerError("kaputt", command=["fail", infile], error_output="kaputt")

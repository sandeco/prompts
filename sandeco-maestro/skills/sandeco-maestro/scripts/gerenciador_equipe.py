"""
Gerenciador de Esquadrão SandecoMaestro
========================================
Script para automação do gerenciamento de atividades
e comunicação entre agentes do esquadrão.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime


PASTA_ESQUADRAO = ".agent/skills/sandeco-maestro/.antigravity/equipe"


class GerenciadorEsquadrao:
    """Classe responsável por orquestrar toda a infraestrutura
    de comunicação e atividades do esquadrão multi-agente."""

    def __init__(self, diretorio_base: str = PASTA_ESQUADRAO):
        self._diretorio_base = Path(diretorio_base)
        self._caminho_registro = self._diretorio_base / "registro_atividades.json"
        self._caminho_caixa_entrada = self._diretorio_base / "caixa_entrada"
        self._caminho_travas = self._diretorio_base / "travas"
        self._caminho_aviso_geral = self._diretorio_base / "aviso_geral.msg"

    def preparar_infraestrutura(self) -> None:
        """Monta todas as pastas e arquivos necessários para o esquadrão funcionar."""
        self._caminho_caixa_entrada.mkdir(parents=True, exist_ok=True)
        self._caminho_travas.mkdir(parents=True, exist_ok=True)

        if not self._caminho_registro.exists():
            conteudo_inicial = {"atividades": [], "integrantes": []}
            self._caminho_registro.write_text(
                json.dumps(conteudo_inicial, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        if not self._caminho_aviso_geral.exists():
            self._caminho_aviso_geral.write_text("", encoding="utf-8")

        print("[OK] Infraestrutura do Esquadrão SandecoMaestro preparada com sucesso.")

    def criar_atividade(
        self,
        titulo: str,
        responsavel: str,
        pre_requisitos: list[int] | None = None,
    ) -> dict:
        """Registra uma nova atividade com suporte a pré-requisitos."""
        dados = self._carregar_registro()

        nova_atividade = {
            "id": len(dados["atividades"]) + 1,
            "titulo": titulo,
            "estado": "PENDENTE",
            "plano_validado": False,
            "responsavel": responsavel,
            "pre_requisitos": pre_requisitos or [],
            "criado_em": datetime.now().isoformat(),
        }

        dados["atividades"].append(nova_atividade)
        self._salvar_registro(dados)

        print(
            f"[OK] Atividade #{nova_atividade['id']} "
            f"({titulo}) atribuída a {responsavel}."
        )
        return nova_atividade

    def comunicado_geral(self, remetente: str, conteudo: str) -> None:
        """Transmite uma mensagem para todos os integrantes do esquadrão."""
        comunicado = {
            "remetente": remetente,
            "categoria": "COMUNICADO_GERAL",
            "conteudo": conteudo,
            "enviado_em": datetime.now().isoformat(),
        }
        with open(self._caminho_aviso_geral, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(comunicado, ensure_ascii=False) + "\n")

        print(f"[OK] Comunicado geral transmitido por {remetente}.")

    def mensagem_direta(self, remetente: str, destinatario: str, conteudo: str) -> None:
        """Envia uma mensagem à caixa de entrada de um agente específico."""
        mensagem = {
            "remetente": remetente,
            "conteudo": conteudo,
            "enviado_em": datetime.now().isoformat(),
        }
        caminho_destino = self._caminho_caixa_entrada / f"{destinatario}.msg"
        with open(caminho_destino, "a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(mensagem, ensure_ascii=False) + "\n")

        print(f"[OK] Mensagem enviada de {remetente} para {destinatario}.")

    def consultar_atividades(self) -> list[dict]:
        """Retorna a lista completa de atividades registradas."""
        dados = self._carregar_registro()
        return dados["atividades"]

    def atualizar_estado(self, id_atividade: int, novo_estado: str) -> None:
        """Atualiza o estado de uma atividade pelo seu ID."""
        dados = self._carregar_registro()

        for atividade in dados["atividades"]:
            if atividade["id"] == id_atividade:
                atividade["estado"] = novo_estado
                self._salvar_registro(dados)
                print(
                    f"[OK] Atividade #{id_atividade} atualizada para estado '{novo_estado}'."
                )
                return

        print(f"[ERRO] Atividade #{id_atividade} não encontrada.")

    def _carregar_registro(self) -> dict:
        """Carrega o arquivo de registro de atividades."""
        conteudo = self._caminho_registro.read_text(encoding="utf-8")
        return json.loads(conteudo)

    def _salvar_registro(self, dados: dict) -> None:
        """Persiste os dados no arquivo de registro."""
        self._caminho_registro.write_text(
            json.dumps(dados, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def principal():
    """Ponto de entrada para execução via linha de comando."""
    gerenciador = GerenciadorEsquadrao()

    if len(sys.argv) < 2:
        print("Uso: python gerenciador_equipe.py <comando> [argumentos...]")
        print("Comandos disponíveis: iniciar, criar_atividade, comunicado_geral, mensagem_direta, listar, atualizar_estado")
        sys.exit(1)

    comando = sys.argv[1]

    if comando == "iniciar":
        gerenciador.preparar_infraestrutura()

    elif comando == "criar_atividade":
        if len(sys.argv) < 4:
            print("Uso: python gerenciador_equipe.py criar_atividade <titulo> <responsavel> [pre_req1,pre_req2,...]")
            sys.exit(1)
        titulo = sys.argv[2]
        responsavel = sys.argv[3]
        pre_requisitos = []
        if len(sys.argv) > 4:
            pre_requisitos = [int(p) for p in sys.argv[4].split(",")]
        gerenciador.criar_atividade(titulo, responsavel, pre_requisitos)

    elif comando == "comunicado_geral":
        if len(sys.argv) < 4:
            print("Uso: python gerenciador_equipe.py comunicado_geral <remetente> <conteudo>")
            sys.exit(1)
        gerenciador.comunicado_geral(sys.argv[2], sys.argv[3])

    elif comando == "mensagem_direta":
        if len(sys.argv) < 5:
            print("Uso: python gerenciador_equipe.py mensagem_direta <remetente> <destinatario> <conteudo>")
            sys.exit(1)
        gerenciador.mensagem_direta(sys.argv[2], sys.argv[3], sys.argv[4])

    elif comando == "listar":
        atividades = gerenciador.consultar_atividades()
        if not atividades:
            print("Nenhuma atividade registrada.")
        for ativ in atividades:
            print(f"  #{ativ['id']} [{ativ['estado']}] {ativ['titulo']} → {ativ['responsavel']}")

    elif comando == "atualizar_estado":
        if len(sys.argv) < 4:
            print("Uso: python gerenciador_equipe.py atualizar_estado <id> <novo_estado>")
            sys.exit(1)
        gerenciador.atualizar_estado(int(sys.argv[2]), sys.argv[3])

    else:
        print(f"[ERRO] Comando '{comando}' não reconhecido.")
        sys.exit(1)


if __name__ == "__main__":
    principal()

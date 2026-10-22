import html
import json
import os
import smtplib
import threading
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.config import settings
from backend.app.engine.orchestrator import orchestrator
from backend.app.services.contacts_service import contacts_service


class EmailService:
    """
    Serviço de compilação de ordens passíveis de erro e disparo de e-mails para contatos industriais.
    """

    def __init__(self):
        self.sent_file = Path(settings.SENT_EMAILS_FILE)
        self._lock = threading.Lock()
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        self.sent_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.sent_file.exists():
            with open(self.sent_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _log_sent_email(self, record: Dict[str, Any]) -> None:
        with self._lock:
            try:
                self._ensure_storage()
                data = []
                if self.sent_file.exists():
                    try:
                        with open(self.sent_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if not isinstance(data, list):
                                data = []
                    except Exception:
                        data = []
                data.append(record)
                temp = self.sent_file.with_suffix(".tmp")
                with open(temp, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                temp.replace(self.sent_file)
            except Exception:
                pass

    def get_greeting(self) -> str:
        """
        Retorna 'Bom dia' ou 'Boa tarde' a depender do horário local.
        """
        current_hour = datetime.now().hour
        return "Bom dia" if current_hour < 12 else "Boa tarde"

    def get_execution_data(
        self, execution_id: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int, str]:
        """
        Recupera os registros de resultado, dias_uteis e data_ref da execução indicada ou da mais recente.
        """
        ctx = None
        if execution_id and execution_id != "latest":
            ctx = orchestrator.get_context(execution_id)
        else:
            # Pega o contexto mais recente
            contexts = list(orchestrator._contexts.values())
            if contexts:
                ctx = contexts[-1]

        if not ctx:
            return [], 3, ""

        dias_uteis = getattr(ctx, "dias_uteis", 3)
        data_ref = getattr(ctx, "data_ref", "")

        records: List[Dict[str, Any]] = []
        if ctx.final_response and "records" in ctx.final_response:
            records = ctx.final_response["records"]
        elif hasattr(ctx, "divergences_df") and not ctx.divergences_df.empty:
            records = ctx.divergences_df.to_dict(orient="records")

        return records, dias_uteis, data_ref

    def filter_errors_for_contact(
        self, records: List[Dict[str, Any]], locais: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filtra ordens passíveis de erro pertencentes aos locais de produção do contato.
        """
        if not records or not locais:
            return []

        target_locais = {str(l).strip().upper() for l in locais if str(l).strip()}
        filtered: List[Dict[str, Any]] = []

        for r in records:
            # Considera apenas divergências/erros reais (ignora status OK)
            status = str(r.get("status_divergencia", "")).upper()
            sev = str(r.get("severidade", "")).upper()
            deficit = float(r.get("deficit_saldo", 0.0) or 0.0)

            is_error = (status != "OK") and (sev != "OK" or deficit > 0)
            if not is_error:
                continue

            r_local = str(r.get("local_producao", "")).strip().upper()
            r_fab = str(r.get("fabrica", "")).strip().upper()

            if r_local in target_locais or r_fab in target_locais:
                filtered.append(r)

        return filtered

    def build_email_content(
        self,
        contact_name: str,
        locais: List[str],
        error_records: List[Dict[str, Any]],
        dias_uteis: int = 3,
        data_ref: str = "",
    ) -> Tuple[str, str, str]:
        """
        Gera o assunto, corpo em texto puro e corpo formatado em HTML.
        Mensagem obrigatória:
        "(Bom dia ou boa tarde a depender do horário), (Nome do contato) segue lista de erros de apontamento dos próximos x dias."
        """
        saudacao = self.get_greeting()
        nome = contact_name.strip()
        locais_str = ", ".join(sorted(locais))
        data_ref_str = f" (Ref: {data_ref})" if data_ref else ""

        subject = f"Erros de Apontamento - {locais_str} - Próximos {dias_uteis} dias úteis"

        # Mensagem textual padrão conforme especificação
        frase_abertura = f"{saudacao}, {nome} segue lista de erros de apontamento dos próximos {dias_uteis} dias."

        # Versão Plain Text com resuminho e tabela (sem cabeçalho decorativo)
        lines = [
            frase_abertura,
            "",
            f"Locais atribuídos: {locais_str}{data_ref_str}",
            f"Total de ordens passíveis de erro: {len(error_records)}",
            "-" * 90,
        ]

        if not error_records:
            lines.append("Nenhum erro de apontamento identificado para os seus locais nesta janela.")
        else:
            lines.append(
                f"{'OP':<12} | {'Produto':<24} | {'Componente':<18} | {'Local':<12} | {'Entrega':<10} | {'Déficit':<8} | {'Status'}"
            )
            lines.append("-" * 90)
            for r in error_records:
                op = str(r.get("op", ""))[:12]
                prod = str(r.get("produto_op", ""))[:24]
                comp = str(r.get("codigo_componente", ""))[:18]
                loc = str(r.get("local_producao", ""))[:12]
                ent = str(r.get("data_entrega", ""))[:10]
                defic = f"{float(r.get('deficit_saldo', 0)):.1f}"
                stat = str(r.get("status_divergencia", ""))
                lines.append(f"{op:<12} | {prod:<24} | {comp:<18} | {loc:<12} | {ent:<10} | {defic:<8} | {stat}")

        plain_text = "\n".join(lines)

        # Versão HTML simples (sem cabeçalhos rebuscados, apenas o texto de apresentação e a tabela)
        table_rows_html = ""
        if error_records:
            for r in error_records:
                op_val = html.escape(str(r.get("op", "")))
                prod_val = html.escape(str(r.get("produto_op", "") or "-"))
                comp_code = html.escape(str(r.get("codigo_componente", "")))
                comp_desc = html.escape(str(r.get("descricao_componente", "")))
                loc_val = html.escape(str(r.get("local_producao", "")))
                ent_val = html.escape(str(r.get("data_entrega", "")))
                qtd_nec = f"{float(r.get('qtd_necessaria', 0)):.2f}"
                saldo_ini = f"{float(r.get('saldo_inicial_local', 0)):.2f}"
                saldo_rem = f"{float(r.get('saldo_remanescente', 0)):.2f}"
                deficit = f"{float(r.get('deficit_saldo', 0)):.2f}"
                status_raw = str(r.get("status_divergencia", ""))

                status_label = (
                    "SALDO ZERADO"
                    if status_raw == "SALDO_ZERADO_NO_LOCAL"
                    else "SALDO INSUFICIENTE"
                )

                table_rows_html += f"""
                <tr>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; font-family: monospace; font-weight: bold;">{op_val}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px;">{prod_val}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px;">
                        <strong>{comp_code}</strong> - {comp_desc}
                    </td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px;">{loc_val}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; font-family: monospace;">{ent_val}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">{qtd_nec}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">{saldo_ini}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">{saldo_rem}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; text-align: right; color: #b91c1c; font-weight: bold;">-{deficit}</td>
                    <td style="border: 1px solid #ccc; padding: 6px 8px; text-align: center;">{status_label}</td>
                </tr>
                """
        else:
            table_rows_html = """
            <tr>
                <td colspan="10" style="border: 1px solid #ccc; padding: 12px; text-align: center; color: #2e7d32;">
                    Nenhum erro de apontamento identificado para os seus locais nesta análise.
                </td>
            </tr>
            """

        html_body = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>{html.escape(subject)}</title>
</head>
<body style="font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #222; margin: 15px; padding: 0;">
    <p style="font-size: 14px; margin: 0 0 14px 0; color: #111;">
        {frase_abertura}
    </p>

    <!-- Resumo dos Locais e Divergências (sem cabeçalho complexo) -->
    <div style="background-color: #F9FAFB; border: 1px solid #E5E7EB; border-left: 4px solid #C49A45; border-radius: 2px; padding: 10px 14px; margin-bottom: 16px; font-size: 12px;">
        <div style="margin-bottom: 3px;"><strong>Locais de Produção:</strong> <span style="color: #374151;">{html.escape(locais_str)}</span></div>
        <div style="margin-bottom: 3px;"><strong>Janela Considerada:</strong> <span style="color: #374151;">Próximos {dias_uteis} dias úteis{data_ref_str}</span></div>
        <div><strong>Total de Erros de Apontamento:</strong> <span style="color: {'#B91C1C' if error_records else '#059669'}; font-weight: bold;">{len(error_records)} divergência(s)</span></div>
    </div>

    <table style="border-collapse: collapse; width: 100%; border: 1px solid #ccc; font-size: 12px;">
        <thead>
            <tr style="background-color: #f2f2f2;">
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: left;">OP</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: left;">Produto</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: left;">Componente</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: left;">Local</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: left;">Entrega</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">Qtd Nec.</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">Saldo Local</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">Saldo Rem.</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: right;">Déficit</th>
                <th style="border: 1px solid #ccc; padding: 6px 8px; text-align: center;">Status</th>
            </tr>
        </thead>
        <tbody>
            {table_rows_html}
        </tbody>
    </table>
</body>
</html>"""

        return subject, plain_text, html_body

    def send_email(
        self,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str,
    ) -> Dict[str, Any]:
        """
        Envia e-mail via servidor SMTP ou simula e registra em arquivo se SMTP não estiver configurado.
        """
        now_iso = datetime.now().isoformat()
        log_record = {
            "timestamp": now_iso,
            "to": to_email,
            "subject": subject,
            "status": "PENDING",
            "message": "",
        }

        # Modo Simulação (caso SMTP não esteja configurado ou contenha credenciais de exemplo)
        is_simulation = bool(
            not settings.SMTP_HOST
            or settings.SMTP_SIMULATION_MODE
            or not settings.SMTP_HOST.strip()
            or settings.SMTP_USER in ["", "seu_email@gmail.com"]
            or settings.SMTP_PASSWORD in ["", "sua_senha_de_aplicativo_aqui"]
        )

        if is_simulation:
            log_record["status"] = "SIMULATED"
            log_record["message"] = (
                f"E-mail compilado com sucesso e simulado para {to_email}. "
                "Para envio em rede corporativa, configure SMTP_HOST no backend."
            )
            self._log_sent_email(log_record)
            return {
                "status": "SIMULATED",
                "message": log_record["message"],
                "timestamp": now_iso,
            }

        # Disparo Real SMTP
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_email

            part1 = MIMEText(text_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)

            if settings.SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
                if settings.SMTP_USE_TLS:
                    server.starttls()

            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

            server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
            server.quit()

            log_record["status"] = "SENT"
            log_record["message"] = f"E-mail disparado com sucesso para {to_email}."
            self._log_sent_email(log_record)

            return {
                "status": "SENT",
                "message": log_record["message"],
                "timestamp": now_iso,
            }
        except Exception as e:
            err_msg = f"Falha no envio via SMTP ({settings.SMTP_HOST}:{settings.SMTP_PORT}): {str(e)}"
            log_record["status"] = "FAILED"
            log_record["message"] = err_msg
            self._log_sent_email(log_record)
            return {
                "status": "FAILED",
                "message": err_msg,
                "timestamp": now_iso,
            }

    def dispatch_for_contacts(
        self,
        execution_id: Optional[str] = None,
        contact_ids: Optional[List[str]] = None,
        send_all_with_errors: bool = False,
    ) -> Dict[str, Any]:
        """
        Compila e despacha e-mails para os contatos especificados ou para todos que tenham erros.
        """
        all_contacts = contacts_service.list_contacts()
        records, dias_uteis, data_ref = self.get_execution_data(execution_id)

        target_contacts = []
        if send_all_with_errors:
            target_contacts = all_contacts
        elif contact_ids:
            target_set = set(contact_ids)
            target_contacts = [c for c in all_contacts if c.get("id") in target_set]
        else:
            target_contacts = all_contacts

        results = []
        sent_count = 0

        for contact in target_contacts:
            c_id = contact.get("id", "")
            c_name = contact.get("nome", "")
            c_email = contact.get("email", "")
            locais = contact.get("locais", [])

            contact_errors = self.filter_errors_for_contact(records, locais)

            # Se o usuário pediu para enviar apenas para quem tem erro e este não tem, pula
            if send_all_with_errors and not contact_errors:
                results.append({
                    "contact_id": c_id,
                    "contact_name": c_name,
                    "email": c_email,
                    "locais": locais,
                    "total_erros": 0,
                    "status": "SKIPPED_NO_ERRORS",
                    "message": "Nenhum erro de apontamento para os locais atribuídos.",
                })
                continue

            subject, plain_text, html_body = self.build_email_content(
                contact_name=c_name,
                locais=locais,
                error_records=contact_errors,
                dias_uteis=dias_uteis,
                data_ref=data_ref,
            )

            send_res = self.send_email(
                to_email=c_email,
                subject=subject,
                text_content=plain_text,
                html_content=html_body,
            )

            is_ok = send_res.get("status") in ["SENT", "SIMULATED"]
            if is_ok:
                sent_count += 1

            results.append({
                "contact_id": c_id,
                "contact_name": c_name,
                "email": c_email,
                "locais": locais,
                "total_erros": len(contact_errors),
                "status": send_res.get("status"),
                "message": send_res.get("message"),
            })

        return {
            "execution_id": execution_id or "latest",
            "dias_uteis": dias_uteis,
            "data_ref": data_ref,
            "total_processed": len(target_contacts),
            "total_sent": sent_count,
            "results": results,
        }


email_service = EmailService()

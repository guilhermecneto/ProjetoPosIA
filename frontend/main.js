document.addEventListener('DOMContentLoaded', () => {
    // ─── Elementos DOM ───────────────────────────────────────────────
    const tableBody      = document.getElementById('table-body');
    const emptyState     = document.getElementById('empty-state');
    const refreshBtn     = document.getElementById('refresh-btn');
    const searchInput    = document.getElementById('search-input');

    const totalCountEl    = document.getElementById('total-count');
    const aprovadosEl     = document.getElementById('aprovados-count');
    const atencaoEl       = document.getElementById('atencao-count');
    const irregularEl     = document.getElementById('irregular-count');
    const lgpdEl          = document.getElementById('lgpd-count');

    const modalOverlay    = document.getElementById('modal-overlay');
    const modalClose      = document.getElementById('modal-close');
    const macroSection    = document.getElementById('macro-section');

    let certificatesData = [];

    // ─── Carregamento de Dados ───────────────────────────────────────
    async function loadData() {
        try {
            const res = await fetch(`public/dados_extraidos.json?t=${Date.now()}`);
            if (!res.ok) return [];
            return await res.json();
        } catch (e) {
            console.error('Erro ao carregar dados:', e);
            return [];
        }
    }

    async function loadMacroReport() {
        try {
            const res = await fetch(`public/relatorio_ocupacional.json?t=${Date.now()}`);
            if (!res.ok) return null;
            return await res.json();
        } catch (e) {
            return null;
        }
    }

    // ─── Utilitários ─────────────────────────────────────────────────
    function formatDate(ds) {
        if (!ds) return 'N/A';
        const p = ds.split('-');
        return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : ds;
    }

    function scoreColor(n) {
        if (n >= 80) return '#34D399';
        if (n >= 50) return '#FCD34D';
        return '#FB7185';
    }

    function animateCounter(el, end) {
        let start = 0;
        const step = Math.ceil(end / 30);
        const interval = setInterval(() => {
            start = Math.min(start + step, end);
            el.textContent = start;
            if (start >= end) clearInterval(interval);
        }, 30);
    }

    // ─── Renderização da Tabela ──────────────────────────────────────
    function renderTable(data) {
        tableBody.innerHTML = '';

        // Stats
        const total     = data.length;
        const aprovados = data.filter(d => d.auditoria?.status?.toLowerCase() === 'aprovado').length;
        const atencao   = data.filter(d => d.auditoria?.status?.toLowerCase() === 'atenção' || d.auditoria?.status?.toLowerCase() === 'atencao').length;
        const irregular = data.filter(d => d.auditoria?.status?.toLowerCase() === 'irregular').length;
        const lgpd      = data.filter(d => d.privacidade_lgpd?.sucesso_anonimizacao === true).length;

        animateCounter(totalCountEl,  total);
        animateCounter(aprovadosEl,   aprovados);
        animateCounter(atencaoEl,     atencao);
        animateCounter(irregularEl,   irregular);
        animateCounter(lgpdEl,        lgpd);

        if (data.length === 0) {
            emptyState.style.display = 'block';
            tableBody.closest('.table-wrapper').style.display = 'none';
        } else {
            emptyState.style.display = 'none';
            tableBody.closest('.table-wrapper').style.display = 'block';

            data.forEach((item, index) => {
                const tr = document.createElement('tr');
                tr.style.animation = `fadeInUp 0.3s ease-out ${index * 0.04}s both`;

                const statusClass  = (item.auditoria?.status || 'pendente').toLowerCase().replace('ã', 'a');
                const score        = item.auditoria?.score_confianca ?? null;
                const lgpdOk       = item.privacidade_lgpd?.sucesso_anonimizacao === true;
                const especialidade = item.validacao_profissional?.especialidade_detectada || '—';
                const retornoPronto = item.plano_de_retorno_rh?.plano_retorno_gerado === true;
                const diasRetorno   = item.plano_de_retorno_rh?.dias_avaliados || item.dias_afastamento || '—';
                const crmValido     = item.validacao_profissional?.crm_formato_valido;

                const scoreHtml = score !== null
                    ? `<div class="score-bar-wrap">
                         <div class="score-bar"><div class="score-bar-fill" style="width:${score}%;background:${scoreColor(score)}"></div></div>
                         <span style="font-size:0.8rem;color:${scoreColor(score)};font-weight:700;">${score}</span>
                       </div>`
                    : '<span style="color:var(--text-light)">—</span>';

                tr.innerHTML = `
                    <td class="patient-name">${item.nome_paciente || 'N/A'}</td>
                    <td style="color:var(--text-light)">${item.nome_medico || 'N/A'}</td>
                    <td><span class="file-tag">${item.crm || 'N/A'}</span></td>
                    <td class="text-center">${crmValido === true ? '<span class="crm-valid" title="Formato válido">✅</span>' : crmValido === false ? '<span class="crm-invalid" title="Formato inválido">❌</span>' : '—'}</td>
                    <td><span class="badge badge-especialidade">${especialidade}</span></td>
                    <td style="color:var(--text-light)">${formatDate(item.data_atendimento)}</td>
                    <td class="text-center font-weight-bold" style="color:#818CF8">${item.dias_afastamento != null ? item.dias_afastamento + ' dia(s)' : 'N/A'}</td>
                    <td><span class="badge badge-status status-${statusClass}">${item.auditoria?.status || 'Pendente'}</span></td>
                    <td>${scoreHtml}</td>
                    <td class="text-center"><span class="badge ${lgpdOk ? 'badge-lgpd-ok' : 'badge-lgpd-err'}">${lgpdOk ? '🔒 Sim' : '⚠️ Não'}</span></td>
                    <td class="text-center"><span class="badge badge-retorno">${retornoPronto ? '✅ ' + diasRetorno + ' d' : '—'}</span></td>
                    <td><button class="btn-detail" data-index="${index}">Ver detalhes</button></td>
                `;

                // Click na linha ou botão abre modal
                tr.addEventListener('click', () => openModal(item));
                tableBody.appendChild(tr);
            });
        }
    }

    // ─── Modal de Detalhes ───────────────────────────────────────────
    function openModal(item) {
        // Skill 1: Extração
        document.getElementById('modal-paciente-nome').textContent = item.nome_paciente || 'Paciente';
        document.getElementById('modal-arquivo').textContent       = item.arquivo_origem || '';
        document.getElementById('d-nome').textContent              = item.nome_paciente   || 'N/A';
        document.getElementById('d-medico').textContent            = item.nome_medico     || 'N/A';
        document.getElementById('d-crm').textContent               = item.crm             || 'N/A';
        document.getElementById('d-data').textContent              = formatDate(item.data_atendimento);
        document.getElementById('d-dias').textContent              = item.dias_afastamento != null ? item.dias_afastamento + ' dia(s)' : 'N/A';

        // Skill 2: Auditoria
        const audit   = item.auditoria || {};
        const sc      = audit.score_confianca;
        const ststCls = (audit.status || 'pendente').toLowerCase().replace('ã','a');
        document.getElementById('d-audit-status').innerHTML = `<span class="badge badge-status status-${ststCls}">${audit.status || 'N/A'}</span>`;
        document.getElementById('d-audit-score').innerHTML  = sc != null
            ? `<div class="score-bar-wrap"><div class="score-bar"><div class="score-bar-fill" style="width:${sc}%;background:${scoreColor(sc)}"></div></div><strong style="color:${scoreColor(sc)}">${sc}/100</strong></div>`
            : 'N/A';
        const alertasEl = document.getElementById('d-audit-alertas');
        alertasEl.innerHTML = '';
        (audit.alertas || ['Nenhum alerta registrado.']).forEach(a => {
            const li = document.createElement('li'); li.textContent = a; alertasEl.appendChild(li);
        });
        document.getElementById('d-audit-parecer').textContent = audit.parecer_tecnico || '—';

        // Skill 3: Validação CRM
        const val = item.validacao_profissional || {};
        document.getElementById('d-crm-valido').innerHTML     = val.crm_formato_valido === true ? '<span class="badge badge-lgpd-ok">✅ Válido</span>' : val.crm_formato_valido === false ? '<span class="badge badge-lgpd-err">❌ Inválido</span>' : '—';
        document.getElementById('d-especialidade').innerHTML  = `<span class="badge badge-especialidade">${val.especialidade_detectada || '—'}</span>`;
        document.getElementById('d-coerencia').textContent    = val.coerencia_habilitacao || val.coerencia_especialidade_cid || '—';
        document.getElementById('d-alerta-rqe').textContent   = val.alerta_rqe || 'Nenhum alerta.';
        document.getElementById('d-val-conclusao').textContent = val.conclusao_tecnica || '—';

        // Skill 4: LGPD
        const lgpd = item.privacidade_lgpd || {};
        const lgpdOk = lgpd.sucesso_anonimizacao === true;
        document.getElementById('d-lgpd-ok').innerHTML = `<span class="badge ${lgpdOk ? 'badge-lgpd-ok' : 'badge-lgpd-err'}">${lgpdOk ? '🔒 Anonimizado' : '⚠️ Falha'}</span>`;
        const camposEl = document.getElementById('d-lgpd-campos');
        camposEl.innerHTML = '';
        (lgpd.campos_ocultados || []).forEach(c => {
            const span = document.createElement('span'); span.className = 'tag'; span.textContent = c; camposEl.appendChild(span);
        });
        if (!lgpd.campos_ocultados?.length) camposEl.innerHTML = '<span style="color:var(--text-light);font-size:0.85rem">Nenhum campo reportado.</span>';
        document.getElementById('d-lgpd-dias').textContent    = lgpd.dados_seguros_para_rh?.dias_afastamento || item.dias_afastamento || 'N/A';
        document.getElementById('d-lgpd-parecer').textContent = lgpd.parecer_dpo || '—';

        // Skill 5: Retorno
        const ret = item.plano_de_retorno_rh || {};
        document.getElementById('d-retorno-dias').textContent = ret.dias_avaliados || '—';
        const diretrizesEl = document.getElementById('d-retorno-diretrizes');
        diretrizesEl.innerHTML = '';
        (ret.diretrizes_gestor_rh || ['Nenhuma diretriz gerada.']).forEach(d => {
            const li = document.createElement('li'); li.textContent = d; diretrizesEl.appendChild(li);
        });
        document.getElementById('d-retorno-ergonomia').textContent = ret.orientacao_ergonomica_padrao || '—';

        modalOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modalOverlay.style.display = 'none';
        document.body.style.overflow = '';
    }

    modalClose.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (e) => { if (e.target === modalOverlay) closeModal(); });
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

    // ─── Relatório Macro (Skill 6) ───────────────────────────────────
    function renderMacroReport(report) {
        if (!report || !report.analise_macro_gerada) { macroSection.style.display = 'none'; return; }
        macroSection.style.display = 'block';

        const nexo   = report.alerta_nexo_causal_identificado || '';
        const badge  = document.getElementById('macro-nexo-badge');
        if (nexo === 'Sim') { badge.textContent = '🚨 Nexo Causal Identificado'; badge.className = 'nexo-badge nexo-sim'; }
        else if (nexo === 'Não') { badge.textContent = '✅ Sem Nexo Identificado'; badge.className = 'nexo-badge nexo-nao'; }
        else { badge.textContent = '🔍 Requer Investigação'; badge.className = 'nexo-badge nexo-inv'; }

        const riscosEl = document.getElementById('macro-riscos');
        riscosEl.innerHTML = '';
        (report.principais_riscos_mapeados || []).forEach(r => {
            const li = document.createElement('li'); li.textContent = r; riscosEl.appendChild(li);
        });

        const acoesEl = document.getElementById('macro-acoes');
        acoesEl.innerHTML = '';
        (report.plano_acao_preventiva || []).forEach(a => {
            const li = document.createElement('li'); li.textContent = a; acoesEl.appendChild(li);
        });

        document.getElementById('macro-conclusao').textContent = report.conclusao_medicina_trabalho || '—';
    }

    // ─── Busca ───────────────────────────────────────────────────────
    searchInput.addEventListener('input', (e) => {
        const q = e.target.value.toLowerCase();
        const filtered = certificatesData.filter(item =>
            (item.nome_paciente && item.nome_paciente.toLowerCase().includes(q)) ||
            (item.crm && item.crm.toLowerCase().includes(q)) ||
            (item.nome_medico && item.nome_medico.toLowerCase().includes(q))
        );
        renderTable(filtered);
    });

    // ─── Refresh / Init ──────────────────────────────────────────────
    async function refreshDashboard() {
        const icon = refreshBtn.querySelector('.feather-refresh-ccw');
        icon.classList.add('spin-anim');

        certificatesData = await loadData();
        renderTable(certificatesData);

        const macro = await loadMacroReport();
        renderMacroReport(macro);

        setTimeout(() => icon.classList.remove('spin-anim'), 700);
    }

    refreshDashboard();
    refreshBtn.addEventListener('click', refreshDashboard);
});

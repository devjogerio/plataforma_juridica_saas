import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class Processo(models.Model):
    """
    Modelo principal para gestão de processos jurídicos.
    Contém todas as informações essenciais de um processo.
    """
    
    TIPO_PROCESSO_CHOICES = [
        ('judicial', _('Judicial')),
        ('administrativo', _('Administrativo')),
        ('consultivo', _('Consultivo')),
        ('extrajudicial', _('Extrajudicial')),
    ]
    
    STATUS_CHOICES = [
        ('ativo', _('Ativo')),
        ('suspenso', _('Suspenso')),
        ('encerrado', _('Encerrado')),
        ('arquivado', _('Arquivado')),
    ]
    
    AREA_DIREITO_CHOICES = [
        ('civil', _('Direito Civil')),
        ('penal', _('Direito Penal')),
        ('trabalhista', _('Direito Trabalhista')),
        ('tributario', _('Direito Tributário')),
        ('empresarial', _('Direito Empresarial')),
        ('familia', _('Direito de Família')),
        ('consumidor', _('Direito do Consumidor')),
        ('previdenciario', _('Direito Previdenciário')),
        ('administrativo', _('Direito Administrativo')),
        ('constitucional', _('Direito Constitucional')),
        ('ambiental', _('Direito Ambiental')),
        ('imobiliario', _('Direito Imobiliário')),
        ('outro', _('Outro')),
    ]
    
    # Estrutura organizada de comarcas/tribunais por estado
    COMARCAS_TRIBUNAIS_POR_ESTADO = {
        'sp': {
            'label': _('São Paulo'),
            'comarcas': [
                ('sp_capital', _('Comarca da Capital')),
                ('sp_santos', _('Comarca de Santos')),
                ('sp_campinas', _('Comarca de Campinas')),
                ('sp_ribeirao_preto', _('Comarca de Ribeirão Preto')),
                ('sp_sorocaba', _('Comarca de Sorocaba')),
                ('sp_sao_jose_campos', _('Comarca de São José dos Campos')),
                ('sp_bauru', _('Comarca de Bauru')),
                ('sp_piracicaba', _('Comarca de Piracicaba')),
                ('sp_jundiai', _('Comarca de Jundiaí')),
                ('sp_osasco', _('Comarca de Osasco')),
                ('sp_guarulhos', _('Comarca de Guarulhos')),
                ('sp_mogi_cruzes', _('Comarca de Mogi das Cruzes')),
                ('sp_taubaté', _('Comarca de Taubaté')),
                ('sp_marilia', _('Comarca de Marília')),
                ('sp_presidente_prudente', _('Comarca de Presidente Prudente')),
                ('sp_aracatuba', _('Comarca de Araçatuba')),
                ('sp_sao_carlos', _('Comarca de São Carlos')),
                ('sp_franca', _('Comarca de Franca')),
                ('sp_araraquara', _('Comarca de Araraquara')),
                ('sp_americana', _('Comarca de Americana')),
                ('tjsp', _('Tribunal de Justiça de São Paulo')),
                ('trf3', _('Tribunal Regional Federal da 3ª Região')),
            ]
        },
        'rj': {
            'label': _('Rio de Janeiro'),
            'comarcas': [
                ('rj_capital', _('Comarca da Capital')),
                ('rj_niteroi', _('Comarca de Niterói')),
                ('rj_duque_caxias', _('Comarca de Duque de Caxias')),
                ('rj_nova_iguacu', _('Comarca de Nova Iguaçu')),
                ('rj_sao_goncalo', _('Comarca de São Gonçalo')),
                ('rj_campos', _('Comarca de Campos dos Goytacazes')),
                ('rj_petropolis', _('Comarca de Petrópolis')),
                ('rj_volta_redonda', _('Comarca de Volta Redonda')),
                ('rj_nova_friburgo', _('Comarca de Nova Friburgo')),
                ('rj_macae', _('Comarca de Macaé')),
                ('rj_cabo_frio', _('Comarca de Cabo Frio')),
                ('rj_angra_reis', _('Comarca de Angra dos Reis')),
                ('tjrj', _('Tribunal de Justiça do Rio de Janeiro')),
                ('trf2', _('Tribunal Regional Federal da 2ª Região')),
            ]
        },
        'mg': {
            'label': _('Minas Gerais'),
            'comarcas': [
                ('mg_belo_horizonte', _('Comarca de Belo Horizonte')),
                ('mg_uberlandia', _('Comarca de Uberlândia')),
                ('mg_contagem', _('Comarca de Contagem')),
                ('mg_juiz_fora', _('Comarca de Juiz de Fora')),
                ('mg_betim', _('Comarca de Betim')),
                ('mg_montes_claros', _('Comarca de Montes Claros')),
                ('mg_ribeirao_pretas', _('Comarca de Ribeirão das Neves')),
                ('mg_uberaba', _('Comarca de Uberaba')),
                ('mg_governador_valadares', _('Comarca de Governador Valadares')),
                ('mg_ipatinga', _('Comarca de Ipatinga')),
                ('mg_divinopolis', _('Comarca de Divinópolis')),
                ('mg_sete_lagoas', _('Comarca de Sete Lagoas')),
                ('mg_pocos_caldas', _('Comarca de Poços de Caldas')),
                ('mg_patos_minas', _('Comarca de Patos de Minas')),
                ('mg_barbacena', _('Comarca de Barbacena')),
                ('tjmg', _('Tribunal de Justiça de Minas Gerais')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'rs': {
            'label': _('Rio Grande do Sul'),
            'comarcas': [
                ('rs_porto_alegre', _('Comarca de Porto Alegre')),
                ('rs_caxias_sul', _('Comarca de Caxias do Sul')),
                ('rs_pelotas', _('Comarca de Pelotas')),
                ('rs_canoas', _('Comarca de Canoas')),
                ('rs_santa_maria', _('Comarca de Santa Maria')),
                ('rs_gravataí', _('Comarca de Gravataí')),
                ('rs_viamao', _('Comarca de Viamão')),
                ('rs_novo_hamburgo', _('Comarca de Novo Hamburgo')),
                ('rs_sao_leopoldo', _('Comarca de São Leopoldo')),
                ('rs_rio_grande', _('Comarca do Rio Grande')),
                ('rs_alvorada', _('Comarca de Alvorada')),
                ('rs_passo_fundo', _('Comarca de Passo Fundo')),
                ('rs_sapucaia_sul', _('Comarca de Sapucaia do Sul')),
                ('rs_uruguaiana', _('Comarca de Uruguaiana')),
                ('rs_santa_cruz_sul', _('Comarca de Santa Cruz do Sul')),
                ('tjrs', _('Tribunal de Justiça do Rio Grande do Sul')),
                ('trf4', _('Tribunal Regional Federal da 4ª Região')),
            ]
        },
        'pr': {
            'label': _('Paraná'),
            'comarcas': [
                ('pr_curitiba', _('Comarca de Curitiba')),
                ('pr_londrina', _('Comarca de Londrina')),
                ('pr_maringa', _('Comarca de Maringá')),
                ('pr_ponta_grossa', _('Comarca de Ponta Grossa')),
                ('pr_cascavel', _('Comarca de Cascavel')),
                ('pr_sao_jose_pinhais', _('Comarca de São José dos Pinhais')),
                ('pr_foz_iguacu', _('Comarca de Foz do Iguaçu')),
                ('pr_colombo', _('Comarca de Colombo')),
                ('pr_guarapuava', _('Comarca de Guarapuava')),
                ('pr_paranagua', _('Comarca de Paranaguá')),
                ('pr_araucaria', _('Comarca de Araucária')),
                ('pr_toledo', _('Comarca de Toledo')),
                ('pr_apucarana', _('Comarca de Apucarana')),
                ('pr_campo_largo', _('Comarca de Campo Largo')),
                ('pr_arapongas', _('Comarca de Arapongas')),
                ('tjpr', _('Tribunal de Justiça do Paraná')),
                ('trf4', _('Tribunal Regional Federal da 4ª Região')),
            ]
        },
        'sc': {
            'label': _('Santa Catarina'),
            'comarcas': [
                ('sc_florianopolis', _('Comarca de Florianópolis')),
                ('sc_joinville', _('Comarca de Joinville')),
                ('sc_blumenau', _('Comarca de Blumenau')),
                ('sc_sao_jose', _('Comarca de São José')),
                ('sc_criciuma', _('Comarca de Criciúma')),
                ('sc_chapeco', _('Comarca de Chapecó')),
                ('sc_itajai', _('Comarca de Itajaí')),
                ('sc_lages', _('Comarca de Lages')),
                ('sc_palhoça', _('Comarca de Palhoça')),
                ('sc_balneario_camboriu', _('Comarca de Balneário Camboriú')),
                ('sc_brusque', _('Comarca de Brusque')),
                ('sc_tubarao', _('Comarca de Tubarão')),
                ('sc_sao_bento_sul', _('Comarca de São Bento do Sul')),
                ('sc_cacador', _('Comarca de Caçador')),
                ('sc_concordia', _('Comarca de Concórdia')),
                ('tjsc', _('Tribunal de Justiça de Santa Catarina')),
                ('trf4', _('Tribunal Regional Federal da 4ª Região')),
            ]
        },
        'ba': {
            'label': _('Bahia'),
            'comarcas': [
                ('ba_salvador', _('Comarca de Salvador')),
                ('ba_feira_santana', _('Comarca de Feira de Santana')),
                ('ba_vitoria_conquista', _('Comarca de Vitória da Conquista')),
                ('ba_camaçari', _('Comarca de Camaçari')),
                ('ba_itabuna', _('Comarca de Itabuna')),
                ('ba_juazeiro', _('Comarca de Juazeiro')),
                ('ba_lauro_freitas', _('Comarca de Lauro de Freitas')),
                ('ba_ilheus', _('Comarca de Ilhéus')),
                ('ba_jequie', _('Comarca de Jequié')),
                ('ba_teixeira_freitas', _('Comarca de Teixeira de Freitas')),
                ('ba_alagoinhas', _('Comarca de Alagoinhas')),
                ('ba_porto_seguro', _('Comarca de Porto Seguro')),
                ('ba_simoes_filho', _('Comarca de Simões Filho')),
                ('ba_paulo_afonso', _('Comarca de Paulo Afonso')),
                ('ba_eunapolis', _('Comarca de Eunápolis')),
                ('tjba', _('Tribunal de Justiça da Bahia')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'go': {
            'label': _('Goiás'),
            'comarcas': [
                ('go_goiania', _('Comarca de Goiânia')),
                ('go_aparecida_goiania', _('Comarca de Aparecida de Goiânia')),
                ('go_anapolis', _('Comarca de Anápolis')),
                ('go_rio_verde', _('Comarca de Rio Verde')),
                ('go_luziania', _('Comarca de Luziânia')),
                ('go_aguas_lindas', _('Comarca de Águas Lindas de Goiás')),
                ('go_valparaiso', _('Comarca de Valparaíso de Goiás')),
                ('go_trindade', _('Comarca de Trindade')),
                ('go_formosa', _('Comarca de Formosa')),
                ('go_novo_gama', _('Comarca de Novo Gama')),
                ('go_senador_canedo', _('Comarca de Senador Canedo')),
                ('go_catalao', _('Comarca de Catalão')),
                ('go_itumbiara', _('Comarca de Itumbiara')),
                ('go_planaltina', _('Comarca de Planaltina')),
                ('go_caldas_novas', _('Comarca de Caldas Novas')),
                ('tjgo', _('Tribunal de Justiça de Goiás')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'df': {
            'label': _('Distrito Federal'),
            'comarcas': [
                ('df_brasilia', _('Comarca de Brasília')),
                ('df_taguatinga', _('Comarca de Taguatinga')),
                ('df_ceilandia', _('Comarca de Ceilândia')),
                ('df_samambaia', _('Comarca de Samambaia')),
                ('df_planaltina', _('Comarca de Planaltina')),
                ('df_sao_sebastiao', _('Comarca de São Sebastião')),
                ('df_recanto_emas', _('Comarca do Recanto das Emas')),
                ('df_gama', _('Comarca do Gama')),
                ('df_santa_maria', _('Comarca de Santa Maria')),
                ('df_paranoa', _('Comarca do Paranoá')),
                ('df_sobradinho', _('Comarca de Sobradinho')),
                ('df_brazlandia', _('Comarca de Brazlândia')),
                ('tjdft', _('Tribunal de Justiça do Distrito Federal e Territórios')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'ac': {
            'label': _('Acre'),
            'comarcas': [
                ('ac_rio_branco', _('Comarca de Rio Branco')),
                ('ac_cruzeiro_sul', _('Comarca de Cruzeiro do Sul')),
                ('ac_sena_madureira', _('Comarca de Sena Madureira')),
                ('ac_tarauaca', _('Comarca de Tarauacá')),
                ('ac_feijo', _('Comarca de Feijó')),
                ('tjac', _('Tribunal de Justiça do Acre')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'al': {
            'label': _('Alagoas'),
            'comarcas': [
                ('al_maceio', _('Comarca de Maceió')),
                ('al_arapiraca', _('Comarca de Arapiraca')),
                ('al_palmeira_indios', _('Comarca de Palmeira dos Índios')),
                ('al_penedo', _('Comarca de Penedo')),
                ('al_santana_ipanema', _('Comarca de Santana do Ipanema')),
                ('al_uniao_palmares', _('Comarca de União dos Palmares')),
                ('tjal', _('Tribunal de Justiça de Alagoas')),
                ('trf5', _('Tribunal Regional Federal da 5ª Região')),
            ]
        },
        'ap': {
            'label': _('Amapá'),
            'comarcas': [
                ('ap_macapa', _('Comarca de Macapá')),
                ('ap_santana', _('Comarca de Santana')),
                ('ap_laranjal_jari', _('Comarca de Laranjal do Jari')),
                ('ap_oiapoque', _('Comarca de Oiapoque')),
                ('tjap', _('Tribunal de Justiça do Amapá')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'am': {
            'label': _('Amazonas'),
            'comarcas': [
                ('am_manaus', _('Comarca de Manaus')),
                ('am_parintins', _('Comarca de Parintins')),
                ('am_itacoatiara', _('Comarca de Itacoatiara')),
                ('am_tefe', _('Comarca de Tefé')),
                ('am_tabatinga', _('Comarca de Tabatinga')),
                ('am_coari', _('Comarca de Coari')),
                ('am_manacapuru', _('Comarca de Manacapuru')),
                ('tjam', _('Tribunal de Justiça do Amazonas')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'ce': {
            'label': _('Ceará'),
            'comarcas': [
                ('ce_fortaleza', _('Comarca de Fortaleza')),
                ('ce_caucaia', _('Comarca de Caucaia')),
                ('ce_juazeiro_norte', _('Comarca de Juazeiro do Norte')),
                ('ce_maracanau', _('Comarca de Maracanaú')),
                ('ce_sobral', _('Comarca de Sobral')),
                ('ce_crato', _('Comarca do Crato')),
                ('ce_iguatu', _('Comarca de Iguatu')),
                ('ce_quixada', _('Comarca de Quixadá')),
                ('tjce', _('Tribunal de Justiça do Ceará')),
                ('trf5', _('Tribunal Regional Federal da 5ª Região')),
            ]
        },
        'es': {
            'label': _('Espírito Santo'),
            'comarcas': [
                ('es_vitoria', _('Comarca de Vitória')),
                ('es_vila_velha', _('Comarca de Vila Velha')),
                ('es_serra', _('Comarca da Serra')),
                ('es_cariacica', _('Comarca de Cariacica')),
                ('es_cachoeiro_itapemirim', _('Comarca de Cachoeiro de Itapemirim')),
                ('es_linhares', _('Comarca de Linhares')),
                ('es_colatina', _('Comarca de Colatina')),
                ('es_sao_mateus', _('Comarca de São Mateus')),
                ('tjes', _('Tribunal de Justiça do Espírito Santo')),
                ('trf2', _('Tribunal Regional Federal da 2ª Região')),
            ]
        },
        'ma': {
            'label': _('Maranhão'),
            'comarcas': [
                ('ma_sao_luis', _('Comarca de São Luís')),
                ('ma_imperatriz', _('Comarca de Imperatriz')),
                ('ma_timon', _('Comarca de Timon')),
                ('ma_caxias', _('Comarca de Caxias')),
                ('ma_codó', _('Comarca de Codó')),
                ('ma_bacabal', _('Comarca de Bacabal')),
                ('ma_santa_ines', _('Comarca de Santa Inês')),
                ('tjma', _('Tribunal de Justiça do Maranhão')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'mt': {
            'label': _('Mato Grosso'),
            'comarcas': [
                ('mt_cuiaba', _('Comarca de Cuiabá')),
                ('mt_varzea_grande', _('Comarca de Várzea Grande')),
                ('mt_rondonopolis', _('Comarca de Rondonópolis')),
                ('mt_sinop', _('Comarca de Sinop')),
                ('mt_tangara_serra', _('Comarca de Tangará da Serra')),
                ('mt_caceres', _('Comarca de Cáceres')),
                ('mt_barra_garcas', _('Comarca de Barra do Garças')),
                ('tjmt', _('Tribunal de Justiça de Mato Grosso')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'ms': {
            'label': _('Mato Grosso do Sul'),
            'comarcas': [
                ('ms_campo_grande', _('Comarca de Campo Grande')),
                ('ms_dourados', _('Comarca de Dourados')),
                ('ms_tres_lagoas', _('Comarca de Três Lagoas')),
                ('ms_corumba', _('Comarca de Corumbá')),
                ('ms_ponta_pora', _('Comarca de Ponta Porã')),
                ('ms_naviraí', _('Comarca de Naviraí')),
                ('ms_aquidauana', _('Comarca de Aquidauana')),
                ('tjms', _('Tribunal de Justiça de Mato Grosso do Sul')),
                ('trf3', _('Tribunal Regional Federal da 3ª Região')),
            ]
        },
        'pa': {
            'label': _('Pará'),
            'comarcas': [
                ('pa_belem', _('Comarca de Belém')),
                ('pa_ananindeua', _('Comarca de Ananindeua')),
                ('pa_santarem', _('Comarca de Santarém')),
                ('pa_maraba', _('Comarca de Marabá')),
                ('pa_castanhal', _('Comarca de Castanhal')),
                ('pa_abaetetuba', _('Comarca de Abaetetuba')),
                ('pa_parauapebas', _('Comarca de Parauapebas')),
                ('pa_altamira', _('Comarca de Altamira')),
                ('tjpa', _('Tribunal de Justiça do Pará')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'pb': {
            'label': _('Paraíba'),
            'comarcas': [
                ('pb_joao_pessoa', _('Comarca de João Pessoa')),
                ('pb_campina_grande', _('Comarca de Campina Grande')),
                ('pb_santa_rita', _('Comarca de Santa Rita')),
                ('pb_patos', _('Comarca de Patos')),
                ('pb_bayeux', _('Comarca de Bayeux')),
                ('pb_sousa', _('Comarca de Sousa')),
                ('pb_guarabira', _('Comarca de Guarabira')),
                ('tjpb', _('Tribunal de Justiça da Paraíba')),
                ('trf5', _('Tribunal Regional Federal da 5ª Região')),
            ]
        },
        'pe': {
            'label': _('Pernambuco'),
            'comarcas': [
                ('pe_recife', _('Comarca do Recife')),
                ('pe_jaboatao_guararapes', _('Comarca de Jaboatão dos Guararapes')),
                ('pe_olinda', _('Comarca de Olinda')),
                ('pe_caruaru', _('Comarca de Caruaru')),
                ('pe_petrolina', _('Comarca de Petrolina')),
                ('pe_paulista', _('Comarca de Paulista')),
                ('pe_cabo_santo_agostinho', _('Comarca do Cabo de Santo Agostinho')),
                ('pe_garanhuns', _('Comarca de Garanhuns')),
                ('tjpe', _('Tribunal de Justiça de Pernambuco')),
                ('trf5', _('Tribunal Regional Federal da 5ª Região')),
            ]
        },
        'pi': {
            'label': _('Piauí'),
            'comarcas': [
                ('pi_teresina', _('Comarca de Teresina')),
                ('pi_parnaiba', _('Comarca de Parnaíba')),
                ('pi_picos', _('Comarca de Picos')),
                ('pi_floriano', _('Comarca de Floriano')),
                ('pi_piripiri', _('Comarca de Piripiri')),
                ('pi_campo_maior', _('Comarca de Campo Maior')),
                ('pi_bom_jesus', _('Comarca de Bom Jesus')),
                ('tjpi', _('Tribunal de Justiça do Piauí')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'rn': {
            'label': _('Rio Grande do Norte'),
            'comarcas': [
                ('rn_natal', _('Comarca de Natal')),
                ('rn_mossoró', _('Comarca de Mossoró')),
                ('rn_parnamirim', _('Comarca de Parnamirim')),
                ('rn_sao_goncalo_amarante', _('Comarca de São Gonçalo do Amarante')),
                ('rn_macaiba', _('Comarca de Macaíba')),
                ('rn_ceara_mirim', _('Comarca de Ceará-Mirim')),
                ('rn_caico', _('Comarca de Caicó')),
                ('tjrn', _('Tribunal de Justiça do Rio Grande do Norte')),
                ('trf5', _('Tribunal Regional Federal da 5ª Região')),
            ]
        },
        'ro': {
            'label': _('Rondônia'),
            'comarcas': [
                ('ro_porto_velho', _('Comarca de Porto Velho')),
                ('ro_ji_parana', _('Comarca de Ji-Paraná')),
                ('ro_ariquemes', _('Comarca de Ariquemes')),
                ('ro_vilhena', _('Comarca de Vilhena')),
                ('ro_cacoal', _('Comarca de Cacoal')),
                ('ro_rolim_moura', _('Comarca de Rolim de Moura')),
                ('ro_guajara_mirim', _('Comarca de Guajará-Mirim')),
                ('tjro', _('Tribunal de Justiça de Rondônia')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'rr': {
            'label': _('Roraima'),
            'comarcas': [
                ('rr_boa_vista', _('Comarca de Boa Vista')),
                ('rr_caracarai', _('Comarca de Caracaraí')),
                ('rr_rorainopolis', _('Comarca de Rorainópolis')),
                ('rr_sao_luiz', _('Comarca de São Luiz')),
                ('tjrr', _('Tribunal de Justiça de Roraima')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'se': {
            'label': _('Sergipe'),
            'comarcas': [
                ('se_aracaju', _('Comarca de Aracaju')),
                ('se_nossa_senhora_socorro', _('Comarca de Nossa Senhora do Socorro')),
                ('se_lagarto', _('Comarca de Lagarto')),
                ('se_itabaiana', _('Comarca de Itabaiana')),
                ('se_estancia', _('Comarca de Estância')),
                ('se_propriá', _('Comarca de Propriá')),
                ('tjse', _('Tribunal de Justiça de Sergipe')),
                ('trf5', _('Tribunal Regional Federal da 5ª Região')),
            ]
        },
        'to': {
            'label': _('Tocantins'),
            'comarcas': [
                ('to_palmas', _('Comarca de Palmas')),
                ('to_araguaina', _('Comarca de Araguaína')),
                ('to_gurupi', _('Comarca de Gurupi')),
                ('to_porto_nacional', _('Comarca de Porto Nacional')),
                ('to_paraiso_tocantins', _('Comarca de Paraíso do Tocantins')),
                ('to_colinas_tocantins', _('Comarca de Colinas do Tocantins')),
                ('tjto', _('Tribunal de Justiça do Tocantins')),
                ('trf1', _('Tribunal Regional Federal da 1ª Região')),
            ]
        },
        'tribunais_superiores': {
            'label': _('Tribunais Superiores'),
            'comarcas': [
                ('stj', _('Superior Tribunal de Justiça')),
                ('stf', _('Supremo Tribunal Federal')),
                ('tst', _('Tribunal Superior do Trabalho')),
                ('tse', _('Tribunal Superior Eleitoral')),
                ('stm', _('Superior Tribunal Militar')),
            ]
        }
    }

    # Estrutura organizada de varas/órgãos por comarca/tribunal
    VARAS_ORGAOS_POR_COMARCA = {
        'sp_capital': {
            'label': _('Comarca da Capital - SP'),
            'varas': [
                ('sp_capital_1_civel', _('1ª Vara Cível')),
                ('sp_capital_2_civel', _('2ª Vara Cível')),
                ('sp_capital_3_civel', _('3ª Vara Cível')),
                ('sp_capital_4_civel', _('4ª Vara Cível')),
                ('sp_capital_5_civel', _('5ª Vara Cível')),
                ('sp_capital_1_criminal', _('1ª Vara Criminal')),
                ('sp_capital_2_criminal', _('2ª Vara Criminal')),
                ('sp_capital_3_criminal', _('3ª Vara Criminal')),
                ('sp_capital_1_familia', _('1ª Vara de Família e Sucessões')),
                ('sp_capital_2_familia', _('2ª Vara de Família e Sucessões')),
                ('sp_capital_3_familia', _('3ª Vara de Família e Sucessões')),
                ('sp_capital_1_fazenda', _('1ª Vara da Fazenda Pública')),
                ('sp_capital_2_fazenda', _('2ª Vara da Fazenda Pública')),
                ('sp_capital_3_fazenda', _('3ª Vara da Fazenda Pública')),
                ('sp_capital_1_empresarial', _('1ª Vara Empresarial')),
                ('sp_capital_2_empresarial', _('2ª Vara Empresarial')),
                ('sp_capital_juizado_civel', _('Juizado Especial Cível')),
                ('sp_capital_juizado_criminal', _('Juizado Especial Criminal')),
            ]
        },
        'tjsp': {
            'label': _('Tribunal de Justiça de São Paulo'),
            'varas': [
                ('tjsp_1_camara_civel', _('1ª Câmara de Direito Privado')),
                ('tjsp_2_camara_civel', _('2ª Câmara de Direito Privado')),
                ('tjsp_3_camara_civel', _('3ª Câmara de Direito Privado')),
                ('tjsp_4_camara_civel', _('4ª Câmara de Direito Privado')),
                ('tjsp_5_camara_civel', _('5ª Câmara de Direito Privado')),
                ('tjsp_1_camara_criminal', _('1ª Câmara de Direito Criminal')),
                ('tjsp_2_camara_criminal', _('2ª Câmara de Direito Criminal')),
                ('tjsp_3_camara_criminal', _('3ª Câmara de Direito Criminal')),
                ('tjsp_1_camara_publico', _('1ª Câmara de Direito Público')),
                ('tjsp_2_camara_publico', _('2ª Câmara de Direito Público')),
                ('tjsp_3_camara_publico', _('3ª Câmara de Direito Público')),
                ('tjsp_orgao_especial', _('Órgão Especial')),
                ('tjsp_conselho_superior', _('Conselho Superior da Magistratura')),
            ]
        },
        'trf3': {
            'label': _('Tribunal Regional Federal da 3ª Região'),
            'varas': [
                ('trf3_1_turma', _('1ª Turma')),
                ('trf3_2_turma', _('2ª Turma')),
                ('trf3_3_turma', _('3ª Turma')),
                ('trf3_4_turma', _('4ª Turma')),
                ('trf3_5_turma', _('5ª Turma')),
                ('trf3_6_turma', _('6ª Turma')),
                ('trf3_1_vara_sp', _('1ª Vara Federal de São Paulo')),
                ('trf3_2_vara_sp', _('2ª Vara Federal de São Paulo')),
                ('trf3_3_vara_sp', _('3ª Vara Federal de São Paulo')),
                ('trf3_4_vara_sp', _('4ª Vara Federal de São Paulo')),
                ('trf3_5_vara_sp', _('5ª Vara Federal de São Paulo')),
                ('trf3_vara_execucao_fiscal', _('Vara de Execução Fiscal')),
            ]
        },
        'rj_capital': {
            'label': _('Comarca da Capital - RJ'),
            'varas': [
                ('rj_capital_1_civel', _('1ª Vara Cível')),
                ('rj_capital_2_civel', _('2ª Vara Cível')),
                ('rj_capital_3_civel', _('3ª Vara Cível')),
                ('rj_capital_4_civel', _('4ª Vara Cível')),
                ('rj_capital_5_civel', _('5ª Vara Cível')),
                ('rj_capital_1_criminal', _('1ª Vara Criminal')),
                ('rj_capital_2_criminal', _('2ª Vara Criminal')),
                ('rj_capital_3_criminal', _('3ª Vara Criminal')),
                ('rj_capital_1_familia', _('1ª Vara de Família')),
                ('rj_capital_2_familia', _('2ª Vara de Família')),
                ('rj_capital_3_familia', _('3ª Vara de Família')),
                ('rj_capital_1_fazenda', _('1ª Vara da Fazenda Pública')),
                ('rj_capital_2_fazenda', _('2ª Vara da Fazenda Pública')),
                ('rj_capital_juizado_civel', _('Juizado Especial Cível')),
                ('rj_capital_juizado_criminal', _('Juizado Especial Criminal')),
            ]
        },
        # Estrutura genérica para comarcas sem varas específicas definidas
        'generica': {
            'label': _('Varas Genéricas'),
            'varas': [
                ('vara_unica', _('Vara Única')),
                ('1_vara_civel', _('1ª Vara Cível')),
                ('2_vara_civel', _('2ª Vara Cível')),
                ('3_vara_civel', _('3ª Vara Cível')),
                ('1_vara_criminal', _('1ª Vara Criminal')),
                ('2_vara_criminal', _('2ª Vara Criminal')),
                ('1_vara_familia', _('1ª Vara de Família')),
                ('2_vara_familia', _('2ª Vara de Família')),
                ('1_vara_fazenda', _('1ª Vara da Fazenda Pública')),
                ('2_vara_fazenda', _('2ª Vara da Fazenda Pública')),
                ('vara_empresarial', _('Vara Empresarial')),
                ('juizado_civel', _('Juizado Especial Cível')),
                ('juizado_criminal', _('Juizado Especial Criminal')),
                ('juizado_fazenda', _('Juizado Especial da Fazenda Pública')),
                ('vara_execucao_penal', _('Vara de Execução Penal')),
                ('vara_infancia_juventude', _('Vara da Infância e Juventude')),
                ('vara_violencia_domestica', _('Vara de Violência Doméstica')),
            ]
        },
        # Tribunais Superiores
        'stj': {
            'label': _('Superior Tribunal de Justiça'),
            'varas': [
                ('stj_1_secao', _('1ª Seção')),
                ('stj_2_secao', _('2ª Seção')),
                ('stj_3_secao', _('3ª Seção')),
                ('stj_1_turma', _('1ª Turma')),
                ('stj_2_turma', _('2ª Turma')),
                ('stj_3_turma', _('3ª Turma')),
                ('stj_4_turma', _('4ª Turma')),
                ('stj_5_turma', _('5ª Turma')),
                ('stj_6_turma', _('6ª Turma')),
                ('stj_corte_especial', _('Corte Especial')),
            ]
        },
        'stf': {
            'label': _('Supremo Tribunal Federal'),
            'varas': [
                ('stf_1_turma', _('1ª Turma')),
                ('stf_2_turma', _('2ª Turma')),
                ('stf_plenario', _('Plenário')),
            ]
        },
        'tst': {
            'label': _('Tribunal Superior do Trabalho'),
            'varas': [
                ('tst_1_turma', _('1ª Turma')),
                ('tst_2_turma', _('2ª Turma')),
                ('tst_3_turma', _('3ª Turma')),
                ('tst_4_turma', _('4ª Turma')),
                ('tst_5_turma', _('5ª Turma')),
                ('tst_6_turma', _('6ª Turma')),
                ('tst_7_turma', _('7ª Turma')),
                ('tst_8_turma', _('8ª Turma')),
                ('tst_pleno', _('Tribunal Pleno')),
            ]
        },
        'tse': {
            'label': _('Tribunal Superior Eleitoral'),
            'varas': [
                ('tse_plenario', _('Plenário')),
                ('tse_classe_recurso', _('Classe de Recurso')),
                ('tse_classe_consulta', _('Classe de Consulta')),
            ]
        },
        'stm': {
            'label': _('Superior Tribunal Militar'),
            'varas': [
                ('stm_conselho_permanente', _('Conselho Permanente de Justiça')),
                ('stm_conselho_especial', _('Conselho Especial de Justiça')),
                ('stm_tribunal_pleno', _('Tribunal Pleno')),
            ]
        },
        # Tribunais Regionais Federais
        'trf1': {
            'label': _('Tribunal Regional Federal da 1ª Região'),
            'varas': [
                ('trf1_1_turma', _('1ª Turma')),
                ('trf1_2_turma', _('2ª Turma')),
                ('trf1_3_turma', _('3ª Turma')),
                ('trf1_4_turma', _('4ª Turma')),
                ('trf1_5_turma', _('5ª Turma')),
                ('trf1_6_turma', _('6ª Turma')),
                ('trf1_1_vara_federal', _('1ª Vara Federal')),
                ('trf1_2_vara_federal', _('2ª Vara Federal')),
                ('trf1_3_vara_federal', _('3ª Vara Federal')),
                ('trf1_vara_execucao_fiscal', _('Vara de Execução Fiscal')),
            ]
        },
        'trf2': {
            'label': _('Tribunal Regional Federal da 2ª Região'),
            'varas': [
                ('trf2_1_turma', _('1ª Turma')),
                ('trf2_2_turma', _('2ª Turma')),
                ('trf2_3_turma', _('3ª Turma')),
                ('trf2_4_turma', _('4ª Turma')),
                ('trf2_5_turma', _('5ª Turma')),
                ('trf2_6_turma', _('6ª Turma')),
                ('trf2_7_turma', _('7ª Turma')),
                ('trf2_8_turma', _('8ª Turma')),
                ('trf2_1_vara_federal', _('1ª Vara Federal')),
                ('trf2_2_vara_federal', _('2ª Vara Federal')),
                ('trf2_vara_execucao_fiscal', _('Vara de Execução Fiscal')),
            ]
        },
        'trf4': {
            'label': _('Tribunal Regional Federal da 4ª Região'),
            'varas': [
                ('trf4_1_turma', _('1ª Turma')),
                ('trf4_2_turma', _('2ª Turma')),
                ('trf4_3_turma', _('3ª Turma')),
                ('trf4_4_turma', _('4ª Turma')),
                ('trf4_1_vara_federal', _('1ª Vara Federal')),
                ('trf4_2_vara_federal', _('2ª Vara Federal')),
                ('trf4_3_vara_federal', _('3ª Vara Federal')),
                ('trf4_vara_execucao_fiscal', _('Vara de Execução Fiscal')),
            ]
        },
        'trf5': {
            'label': _('Tribunal Regional Federal da 5ª Região'),
            'varas': [
                ('trf5_1_turma', _('1ª Turma')),
                ('trf5_2_turma', _('2ª Turma')),
                ('trf5_3_turma', _('3ª Turma')),
                ('trf5_4_turma', _('4ª Turma')),
                ('trf5_1_vara_federal', _('1ª Vara Federal')),
                ('trf5_2_vara_federal', _('2ª Vara Federal')),
                ('trf5_vara_execucao_fiscal', _('Vara de Execução Fiscal')),
            ]
        },
        'generica': {
            'label': _('Varas Genéricas'),
            'varas': [
                ('vara_civel', _('Vara Cível')),
                ('vara_criminal', _('Vara Criminal')),
                ('vara_familia', _('Vara de Família')),
                ('vara_fazenda', _('Vara da Fazenda Pública')),
                ('vara_trabalho', _('Vara do Trabalho')),
                ('vara_federal', _('Vara Federal')),
                ('vara_execucao', _('Vara de Execução')),
                ('vara_registros_publicos', _('Vara de Registros Públicos')),
            ]
        }
    }

    # Estrutura organizada de tipos de processos por área do direito
    TIPOS_PROCESSO_POR_AREA = {
        'civil': {
            'label': _('Direito Civil'),
            'tipos': [
                ('civil_indenizacao', _('Ação de Indenização')),
                ('civil_cobranca', _('Ação de Cobrança')),
                ('civil_rescisao_contrato', _('Rescisão Contratual')),
                ('civil_danos_morais', _('Danos Morais')),
                ('civil_revisional', _('Ação Revisional')),
                ('civil_consignacao', _('Consignação em Pagamento')),
                ('civil_monitoria', _('Ação Monitória')),
                ('civil_execucao', _('Execução de Título')),
            ]
        },
        'trabalhista': {
            'label': _('Direito Trabalhista'),
            'tipos': [
                ('trab_reclamatoria', _('Reclamatória Trabalhista')),
                ('trab_horas_extras', _('Horas Extras')),
                ('trab_adicional_insalubridade', _('Adicional de Insalubridade')),
                ('trab_adicional_periculosidade', _('Adicional de Periculosidade')),
                ('trab_rescisao_indireta', _('Rescisão Indireta')),
                ('trab_danos_morais', _('Danos Morais Trabalhistas')),
                ('trab_equiparacao_salarial', _('Equiparação Salarial')),
                ('trab_execucao', _('Execução Trabalhista')),
            ]
        },
        'familia': {
            'label': _('Direito de Família'),
            'tipos': [
                ('fam_divorcio', _('Divórcio')),
                ('fam_separacao', _('Separação')),
                ('fam_guarda', _('Guarda de Menores')),
                ('fam_alimentos', _('Pensão Alimentícia')),
                ('fam_investigacao_paternidade', _('Investigação de Paternidade')),
                ('fam_adocao', _('Adoção')),
                ('fam_inventario', _('Inventário')),
                ('fam_partilha', _('Partilha de Bens')),
            ]
        },
        'penal': {
            'label': _('Direito Penal'),
            'tipos': [
                ('penal_defesa', _('Defesa Criminal')),
                ('penal_habeas_corpus', _('Habeas Corpus')),
                ('penal_revisao_criminal', _('Revisão Criminal')),
                ('penal_execucao_penal', _('Execução Penal')),
                ('penal_queixa_crime', _('Queixa-Crime')),
                ('penal_representacao', _('Representação Criminal')),
            ]
        },
        'tributario': {
            'label': _('Direito Tributário'),
            'tipos': [
                ('trib_mandado_seguranca', _('Mandado de Segurança Tributário')),
                ('trib_execucao_fiscal', _('Execução Fiscal')),
                ('trib_repetição_indebito', _('Repetição de Indébito')),
                ('trib_anulacao_debito', _('Anulação de Débito Tributário')),
                ('trib_compensacao', _('Compensação Tributária')),
                ('trib_parcelamento', _('Parcelamento de Débitos')),
            ]
        },
        'empresarial': {
            'label': _('Direito Empresarial'),
            'tipos': [
                ('emp_recuperacao_judicial', _('Recuperação Judicial')),
                ('emp_falencia', _('Falência')),
                ('emp_dissolucao_sociedade', _('Dissolução de Sociedade')),
                ('emp_conflito_societario', _('Conflito Societário')),
                ('emp_propriedade_intelectual', _('Propriedade Intelectual')),
                ('emp_concorrencia_desleal', _('Concorrência Desleal')),
            ]
        },
        'consumidor': {
            'label': _('Direito do Consumidor'),
            'tipos': [
                ('cons_indenizacao', _('Indenização Consumerista')),
                ('cons_vicio_produto', _('Vício do Produto')),
                ('cons_publicidade_enganosa', _('Publicidade Enganosa')),
                ('cons_cobranca_indevida', _('Cobrança Indevida')),
                ('cons_rescisao_contrato', _('Rescisão Contratual')),
            ]
        },
        'previdenciario': {
            'label': _('Direito Previdenciário'),
            'tipos': [
                ('prev_aposentadoria', _('Aposentadoria')),
                ('prev_auxilio_doenca', _('Auxílio-Doença')),
                ('prev_pensao_morte', _('Pensão por Morte')),
                ('prev_auxilio_acidente', _('Auxílio-Acidente')),
                ('prev_revisao_beneficio', _('Revisão de Benefício')),
                ('prev_restabelecimento', _('Restabelecimento de Benefício')),
            ]
        },
        'administrativo': {
            'label': _('Direito Administrativo'),
            'tipos': [
                ('adm_mandado_seguranca', _('Mandado de Segurança')),
                ('adm_acao_popular', _('Ação Popular')),
                ('adm_improbidade', _('Improbidade Administrativa')),
                ('adm_licitacao', _('Licitação e Contratos')),
                ('adm_servidor_publico', _('Servidor Público')),
            ]
        },
        'constitucional': {
            'label': _('Direito Constitucional'),
            'tipos': [
                ('const_habeas_data', _('Habeas Data')),
                ('const_mandado_injuncao', _('Mandado de Injunção')),
                ('const_acao_inconstitucionalidade', _('Ação de Inconstitucionalidade')),
            ]
        },
        'ambiental': {
            'label': _('Direito Ambiental'),
            'tipos': [
                ('amb_acao_civil_publica', _('Ação Civil Pública Ambiental')),
                ('amb_licenciamento', _('Licenciamento Ambiental')),
                ('amb_dano_ambiental', _('Dano Ambiental')),
            ]
        },
        'imobiliario': {
            'label': _('Direito Imobiliário'),
            'tipos': [
                ('imob_usucapiao', _('Usucapião')),
                ('imob_reintegracao_posse', _('Reintegração de Posse')),
                ('imob_despejo', _('Ação de Despejo')),
                ('imob_revisional_aluguel', _('Revisional de Aluguel')),
                ('imob_adjudicacao_compulsoria', _('Adjudicação Compulsória')),
            ]
        },
        'outro': {
            'label': _('Outras Áreas'),
            'tipos': [
                ('outro_consultivo', _('Consultivo')),
                ('outro_extrajudicial', _('Extrajudicial')),
                ('outro_diversos', _('Diversos')),
            ]
        }
    }
    
    INSTANCIA_CHOICES = [
        ('1_instancia', _('1ª Instância')),
        ('2_instancia', _('2ª Instância')),
        ('superior', _('Tribunal Superior')),
        ('supremo', _('Supremo Tribunal')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Identificador único do processo')
    )
    
    numero_processo = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Número do Processo'),
        help_text=_('Número único do processo no tribunal')
    )
    
    tipo_processo = models.CharField(
        max_length=50,
        choices=[],  # Será preenchido dinamicamente
        verbose_name=_('Tipo de Processo')
    )
    
    area_direito = models.CharField(
        max_length=20,
        choices=AREA_DIREITO_CHOICES,
        verbose_name=_('Área do Direito')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name=_('Status')
    )
    
    instancia = models.CharField(
        max_length=15,
        choices=INSTANCIA_CHOICES,
        default='1_instancia',
        verbose_name=_('Instância')
    )
    
    valor_causa = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        blank=True,
        null=True,
        verbose_name=_('Valor da Causa'),
        help_text=_('Valor econômico do processo')
    )
    
    comarca_tribunal = models.CharField(
        max_length=200,
        verbose_name=_('Comarca/Tribunal'),
        help_text=_('Nome da comarca ou tribunal')
    )
    
    vara_orgao = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Vara/Órgão'),
        help_text=_('Vara ou órgão específico')
    )
    
    juiz = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Juiz'),
        help_text=_('Nome do juiz responsável')
    )
    
    data_inicio = models.DateField(
        verbose_name=_('Data de Início'),
        help_text=_('Data de distribuição ou início do processo')
    )
    
    data_encerramento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Encerramento')
    )
    
    assunto = models.CharField(
        max_length=500,
        verbose_name=_('Assunto'),
        help_text=_('Resumo do objeto do processo')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações'),
        help_text=_('Informações adicionais sobre o processo')
    )
    
    # Relacionamentos
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='processos',
        verbose_name=_('Cliente')
    )
    
    usuario_responsavel = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        related_name='processos_responsavel',
        verbose_name=_('Advogado Responsável')
    )
    
    partes_envolvidas = models.ManyToManyField(
        'clientes.ParteEnvolvida',
        through='ProcessoParteEnvolvida',
        blank=True,
        verbose_name=_('Partes Envolvidas')
    )
    
    # Controle
    ativo = models.BooleanField(
        default=True,
        verbose_name=_('Ativo')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Data de Atualização')
    )
    
    class Meta:
        verbose_name = _('Processo')
        verbose_name_plural = _('Processos')
        ordering = ['-data_inicio', 'numero_processo']
        indexes = [
            models.Index(fields=['numero_processo']),
            models.Index(fields=['cliente', '-data_inicio']),
            models.Index(fields=['usuario_responsavel', '-data_inicio']),
            models.Index(fields=['status']),
            models.Index(fields=['area_direito']),
            models.Index(fields=['tipo_processo']),
        ]
    
    def __str__(self):
        return f"{self.numero_processo}"
    
    @property
    def valor_causa_formatado(self):
        """Retorna o valor da causa formatado em moeda brasileira."""
        if self.valor_causa:
            return f"R$ {self.valor_causa:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        return 'Não informado'

    @property
    def responsavel(self):
        return self.usuario_responsavel
    
    @responsavel.setter
    def responsavel(self, value):
        self.usuario_responsavel = value
    
    @property
    def data_distribuicao(self):
        return self.data_inicio
    
    @data_distribuicao.setter
    def data_distribuicao(self, value):
        self.data_inicio = value
    
    @property
    def dias_tramitacao(self):
        """Calcula os dias de tramitação do processo."""
        from datetime import date
        data_fim = self.data_encerramento or date.today()
        return (data_fim - self.data_inicio).days
    
    @property
    def ultimo_andamento(self):
        """Retorna o último andamento do processo."""
        return self.andamentos.order_by('-data_andamento').first()
    
    @property
    def proximos_prazos(self):
        """Retorna os próximos prazos não cumpridos."""
        from datetime import date
        return self.prazos.filter(
            cumprido=False,
            data_limite__gte=date.today()
        ).order_by('data_limite')
    
    def pode_ser_editado_por(self, usuario):
        """Verifica se o usuário pode editar o processo."""
        if usuario.is_administrador:
            return True
        if usuario == self.usuario_responsavel:
            return True
        return False


class ProcessoParteEnvolvida(models.Model):
    """
    Modelo intermediário para relacionar processos com partes envolvidas.
    Permite adicionar informações específicas da relação.
    """
    
    POLO_CHOICES = [
        ('ativo', _('Polo Ativo')),
        ('passivo', _('Polo Passivo')),
        ('terceiro', _('Terceiro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        verbose_name=_('Processo')
    )
    
    parte_envolvida = models.ForeignKey(
        'clientes.ParteEnvolvida',
        on_delete=models.CASCADE,
        verbose_name=_('Parte Envolvida')
    )
    
    polo = models.CharField(
        max_length=10,
        choices=POLO_CHOICES,
        verbose_name=_('Polo'),
        help_text=_('Posição da parte no processo')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Processo - Parte Envolvida')
        verbose_name_plural = _('Processos - Partes Envolvidas')
        unique_together = ['processo', 'parte_envolvida']
    
    def __str__(self):
        return f"{self.processo.numero_processo} - {self.parte_envolvida.nome} ({self.get_polo_display()})"


class Andamento(models.Model):
    """
    Modelo para registrar andamentos processuais.
    Mantém histórico cronológico de todas as movimentações.
    """
    
    TIPO_ANDAMENTO_CHOICES = [
        ('peticao', _('Petição')),
        ('decisao', _('Decisão')),
        ('sentenca', _('Sentença')),
        ('acordao', _('Acórdão')),
        ('intimacao', _('Intimação')),
        ('audiencia', _('Audiência')),
        ('juntada', _('Juntada')),
        ('citacao', _('Citação')),
        ('recurso', _('Recurso')),
        ('despacho', _('Despacho')),
        ('outro', _('Outro')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='andamentos',
        verbose_name=_('Processo')
    )
    
    data_andamento = models.DateField(
        verbose_name=_('Data do Andamento')
    )
    
    tipo_andamento = models.CharField(
        max_length=20,
        choices=TIPO_ANDAMENTO_CHOICES,
        verbose_name=_('Tipo de Andamento')
    )
    
    descricao = models.TextField(
        verbose_name=_('Descrição'),
        help_text=_('Detalhes do andamento processual')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações Internas'),
        help_text=_('Anotações internas sobre o andamento')
    )
    
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário Responsável'),
        help_text=_('Usuário que registrou o andamento')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Andamento')
        verbose_name_plural = _('Andamentos')
        ordering = ['-data_andamento', '-created_at']
        indexes = [
            models.Index(fields=['processo', '-data_andamento']),
            models.Index(fields=['tipo_andamento']),
            models.Index(fields=['data_andamento']),
        ]
    
    def __str__(self):
        return f"{self.get_tipo_andamento_display()} - {self.processo.numero_processo}"


class Prazo(models.Model):
    """
    Modelo para controle de prazos processuais.
    Gerencia datas limite e alertas automáticos.
    """
    
    TIPO_PRAZO_CHOICES = [
        ('contestacao', _('Contestação')),
        ('recurso', _('Recurso')),
        ('manifestacao', _('Manifestação')),
        ('audiencia', _('Audiência')),
        ('pericia', _('Perícia')),
        ('cumprimento', _('Cumprimento de Sentença')),
        ('embargos', _('Embargos')),
        ('alegacoes', _('Alegações Finais')),
        ('outro', _('Outro')),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', _('Baixa')),
        ('media', _('Média')),
        ('alta', _('Alta')),
        ('critica', _('Crítica')),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    processo = models.ForeignKey(
        Processo,
        on_delete=models.CASCADE,
        related_name='prazos',
        verbose_name=_('Processo')
    )
    
    tipo_prazo = models.CharField(
        max_length=20,
        choices=TIPO_PRAZO_CHOICES,
        verbose_name=_('Tipo de Prazo')
    )
    
    data_limite = models.DateField(
        verbose_name=_('Data Limite'),
        help_text=_('Data final para cumprimento do prazo')
    )
    
    data_inicio = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Início'),
        help_text=_('Data de início da contagem do prazo')
    )
    
    descricao = models.TextField(
        verbose_name=_('Descrição'),
        help_text=_('Detalhes sobre o que deve ser feito')
    )
    
    prioridade = models.CharField(
        max_length=10,
        choices=PRIORIDADE_CHOICES,
        default='media',
        verbose_name=_('Prioridade')
    )
    
    cumprido = models.BooleanField(
        default=False,
        verbose_name=_('Cumprido'),
        help_text=_('Indica se o prazo foi cumprido')
    )
    
    data_cumprimento = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Data de Cumprimento')
    )
    
    observacoes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Observações')
    )
    
    usuario_responsavel = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.PROTECT,
        verbose_name=_('Usuário Responsável')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Data de Criação')
    )
    
    class Meta:
        verbose_name = _('Prazo')
        verbose_name_plural = _('Prazos')
        ordering = ['data_limite', 'prioridade']
        indexes = [
            models.Index(fields=['processo', 'data_limite']),
            models.Index(fields=['data_limite', 'cumprido']),
            models.Index(fields=['usuario_responsavel', 'data_limite']),
            models.Index(fields=['prioridade']),
        ]
    
    def __str__(self):
        titulo = self.descricao or self.get_tipo_prazo_display()
        return f"{titulo} - {self.data_limite.strftime('%d/%m/%Y')}"
    
    @property
    def dias_restantes(self):
        """Calcula quantos dias restam para o prazo."""
        from datetime import date
        if self.cumprido:
            return 0
        
        hoje = date.today()
        if self.data_limite < hoje:
            return (hoje - self.data_limite).days * -1  # Prazo vencido (negativo)
        return (self.data_limite - hoje).days
    
    @property
    def status_prazo(self):
        """Retorna o status do prazo baseado nos dias restantes."""
        if self.cumprido:
            return 'cumprido'
        
        dias = self.dias_restantes
        if dias < 0:
            return 'vencido'
        elif dias <= 3:
            return 'critico'
        elif dias <= 7:
            return 'atencao'
        else:
            return 'normal'
    
    def marcar_como_cumprido(self, data_cumprimento=None):
        """Marca o prazo como cumprido."""
        from datetime import date
        self.cumprido = True
        self.data_cumprimento = data_cumprimento or date.today()
        self.save()
    
    @property
    def data_vencimento(self):
        return self.data_limite
    
    @data_vencimento.setter
    def data_vencimento(self, value):
        self.data_limite = value

    @property
    def responsavel(self):
        return self.usuario_responsavel
    
    @responsavel.setter
    def responsavel(self, value):
        self.usuario_responsavel = value
    
    def clean(self):
        """Validação customizada do modelo."""
        from django.core.exceptions import ValidationError
        from datetime import date
        
        if self.data_inicio and self.data_limite:
            if self.data_inicio > self.data_limite:
                raise ValidationError({
                    'data_limite': _('A data limite deve ser posterior à data de início')
                })
        
        if self.cumprido and not self.data_cumprimento:
            self.data_cumprimento = date.today()

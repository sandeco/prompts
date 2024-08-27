from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

serper = SerperDevTool()

serper.locale = "pt-br"
serper.n_results = 50
serper.country = "br"
serper.location = "Natal, State of Rio Grande do Norte, Brazil"

query = "site:instagram.com sandeco"

agente_pesquisa = Agent(
    role='Agente de Pesquisa',
    goal='Obter resultados de pesquisa paginados da API Serper para o termo {query}',
    backstory='Você é especializado em recuperar dados da web via pesquisa',
    verbose=True,
    memory=True,
    max_iter=2,
    max_rpm=4,
    max_execution_time=120,
    max_retry_limit=3,
    tools=[serper]
)

# Tarefa de extração de informações
extrair_informacoes_site = Task(
    description='Extrair informações detalhadas sobre os serviços, produtos e operações da empresa a partir do site {site_url}.',
    expected_output='Um relatório detalhado contendo as informações sobre serviços, produtos e operações da empresa.',

    agent=agente_pesquisa
)


crew = Crew(
    agents=[agente_pesquisa],
    tasks=[extrair_informacoes_site],
    process=Process.sequential
)


# Executando a tripulação
result = crew.kickoff(inputs={'query': query})

import os
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew, Process

os.environ["OPENAI_API_KEY"] = "sk-proj-1111"

ollama = ChatOpenAI(
    model="llama3.1:8b",
    base_url="http://localhost:11434"
)

# Criando o agente de escrita
agente_escritor = Agent(
    role='Escritor de Cartas de Amor',
    goal='Escreva uma carta de amor para {nome_destinatario}, '
         'expressando os seguintes sentimentos: {sentimentos}."',
    verbose=True,
    memory=True,
    llm=ollama,
    backstory='Você é um poeta experiente, '
              'conhecido por sua habilidade de expressar sentimentos '
              'profundos em palavras.'
)

# Definindo a tarefa que o agente irá executar
tarefa_escrita_carta = Task(
    description="Escrever uma carta de amor para o destinatário especificado.",
    expected_output="Uma carta de amor escrita com palavras sinceras e emocionantes.",
    agent=agente_escritor,
    output_file="amor.md"
)

# Criando a Crew com o agente e a tarefa
equipe = Crew(
    agents=[agente_escritor],
    tasks=[tarefa_escrita_carta],
    process=Process.sequential
)

# Executando o processo com o nome do destinatário e sentimentos desejados
nome_destinatario = "Maria"
sentimentos = "amor eterno, carinho profundo, e admiração"
resultados = equipe.kickoff(inputs={'nome_destinatario': nome_destinatario, 'sentimentos': sentimentos})

print("Carta de Amor:\n", resultados)

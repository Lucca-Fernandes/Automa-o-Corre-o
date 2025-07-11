from utils import extract_github_url, download_file_content
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import requests
import re

# Configuração do Selenium
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 10)

# Configuração da API Key do Gemini
GEMINI_API_KEY = "AIzaSyATAnW2GlSi8xEnrB2azZwgiHbLhfHG3bs"

# Função para login na plataforma
def login_to_platform():
    driver.get("https://apps.projetodesenvolve.online/authn/login")
    time.sleep(2)
    try:
        driver.find_element(By.ID, "emailOrUsername").send_keys("lucca@projetodesenvolve.com.br")
        driver.find_element(By.ID, "password").send_keys("6683@desenvolve")
        driver.find_element(By.ID, "sign-in").click()
        wait.until(EC.presence_of_element_located((By.XPATH, "//a[@data-testid='CourseCardTitle' and text()='JavaScript']")))
        print("Login realizado com sucesso.")
    except Exception as e:
        print(f"Falha no login: {e}")
        raise

# Função para avaliar com IA usando Gemini API
def evaluate_with_ia(prompts, js_code):
    api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=" + GEMINI_API_KEY
    headers = {"Content-Type": "application/json"}
    prompt_list = "\n".join([f"Prompt: {p}" for p in prompts])
    data = {
        "contents": [{
            "parts": [{
                "text": f"Analise o seguinte código JavaScript: {js_code}\n\nVerifique se o código corresponde ao seguinte prompt:\n{prompt_list}\n\nEscolha o prompt mais apropriado (deve ser o único fornecido) e retorne uma nota de 0 a 10 com justificativa. Avalie considerando a intenção do aluno, dando prioridade à funcionalidade e levando em conta esforços parciais. Use os critérios: 70% funcionalidade, 20% legibilidade, 10% comentários. Se o código não corresponder ao prompt, retorne 'Nota: 0/10\nJustificativa: O código não atende ao prompt especificado.'\n\nRetorne no formato: 'Nota: [nota]/10\nJustificativa: [justificativa]'"
            }]
        }],
        "generationConfig": {"maxOutputTokens": 200, "temperature": 0.7}
    }
    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        match = re.search(r"Nota:\s*(\d+(\.\d+)?)/10", result)
        if match:
            note = float(match.group(1))
            print(result)
            return min(max(note, 0), 10)
        print(f"Resposta da IA: {result}. Avaliação rejeitada.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na API do Gemini: {e}. Avaliação rejeitada.")
        return None

# Função para mapear nota para avaliação
def map_note_to_rating(note):
    if 0 <= note <= 3: return "Poor"
    elif 4 <= note <= 6: return "Fair"
    elif 7 <= note <= 8: return "Good"
    elif 9 <= note <= 10: return "Excellent"
    return "Good"

# Função para marcar a nota na plataforma
def mark_grade(note, driver, wait, exercicio_num):
    try:
        start_grading_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'btn-primary') and contains(text(), 'Start grading')]")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", start_grading_button)
        start_grading_button.click()
        print(f"Botão 'Start grading' clicado com sucesso para exercício {exercicio_num}.")
        time.sleep(2)

        radios = driver.find_elements(By.TAG_NAME, "input")
        print("Radio inputs disponíveis após Start grading:", [(r.get_attribute("id"), r.get_attribute("name"), r.get_attribute("value")) for r in radios if r.get_attribute("type") == "radio"])

        rating = map_note_to_rating(note)
        print(f"Nota {note} mapeada para rating: {rating}")

        ideas_rating = "Good" if rating == "Excellent" else rating
        print(f"Rating ajustado para 'Ideas': {ideas_rating}")

        ideas_radio = wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@name='Ideas' and @value='{ideas_rating}']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ideas_radio)
        ideas_radio.click()
        print(f"Radio 'Ideas' marcado como '{ideas_rating}' para exercício {exercicio_num}.")

        content_radio = wait.until(EC.element_to_be_clickable((By.XPATH, f"//input[@name='Content' and @value='{rating}']")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", content_radio)
        content_radio.click()
        print(f"Radio 'Content' marcado como '{rating}' para exercício {exercicio_num}.")

        submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pgn__stateful-btn') and .//span[text()='Submit grade']]")))
        print(f"Botão 'Submit grade' encontrado: {submit_button.is_displayed()}")
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
        submit_button.click()
        print(f"Botão 'Submit grade' clicado com sucesso para exercício {exercicio_num}.")
        wait.until(EC.staleness_of(submit_button))
        time.sleep(2)  # Aumentar o tempo de espera após submissão

    except Exception as e:
        print(f"Falha ao marcar a nota ou submeter para exercício {exercicio_num}: {e}. Tentando novamente...")
        try:
            time.sleep(1)
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'pgn__stateful-btn') and .//span[text()='Submit grade']]")))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_button)
            submit_button.click()
            print(f"Botão 'Submit grade' clicado com sucesso na tentativa extra para exercício {exercicio_num}.")
            wait.until(EC.staleness_of(submit_button))
            time.sleep(2)
        except Exception as e2:
            print(f"Falha na tentativa extra: {e2}. Elementos disponíveis:", [e.get_attribute("outerHTML") for e in driver.find_elements(By.TAG_NAME, "button")])

# Função para avaliar exercícios de JavaScript
def evaluate_javascript():
    course_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[@data-testid='CourseCardTitle' and text()='JavaScript']")))
    course_link.click()
    time.sleep(1)

    # Lista de todos os prompts
    all_prompts = [
        "Crie 5 funções (Soma, Subtrai, Multiplica, Divide, MostraResultado) que realizem operações matemáticas com dois números, usando function ou arrow function. Soma e Subtrai retornam a soma e diferença, Multiplica e Divide retornam o produto e quociente, e MostraResultado exibe no console o nome da operação e resultado no formato 'console.log([nome_da_operacao] entre ${num1} e ${num2}, fn(num1, num2))'. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Crie um temporizador de contagem regressiva que aceita uma data futura, calcula o tempo restante (dias, horas, minutos, segundos) com calcularTempoRestante(dataFutura), atualiza a tela com atualizarTemporizador(), e usa setInterval para atualizar a cada segundo, manipulando o objeto Date. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Altere a questão 2 do exercício anterior (Curtir) para armazenar no localStorage a lista de pessoas que clicaram no botão Curtir, garantindo que a lista persista mesmo após recarregar a página. Adicione também um botão 'Limpar' que remova todos os nomes do localStorage e atualize a visualização. Mantenha a lógica de verificação de duplicatas e a exibição dinâmica da mensagem, com base no número de pessoas que curtiram. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Modifique a lista de tarefas do exercício 6 para usar localStorage, persistindo tarefas ao recarregar, e adicione um botão para excluir tarefas do array e localStorage. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Construa uma página HTML com um campo de texto, um botão 'Curtir' e um parágrafo, armazenando nomes em um array e atualizando o parágrafo conforme: 'Ninguém curtiu' (lista vazia), '[Nome] curtiu' (1 pessoa), '[Pessoa 1] e [Pessoa 2] curtiram' (2 pessoas), '[Pessoa 1], [Pessoa 2] e mais [n-2] pessoas curtiram' (3+ pessoas), verificando duplicatas. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Crie um array de objetos Tarefa (descrição, status) com um campo de texto, botão 'adicionar' para incluir tarefas, checkboxes para alterar o status, e estilização CSS para diferenciar concluídas de não concluídas. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Crie uma aplicação web com um campo de busca e botão que pesquise usuários na API do GitHub, exibindo os dados em uma lista ou 'Não foram encontrados usuários para esta pesquisa' se não houver resultados. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Crie um feed com um formulário fixo (textarea e botão Postar), uma lista de postagens (nome de usuário, avatar, texto, imagem de gato da API https://api.thecatapi.com/v1/images/search, botão curtir) em um array de objetos (data, nome, avatar, texto, imagem, likes), atualizando likes ao clicar. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários.",
        "Crie um sistema para gerenciar o estoque de uma livraria com um array de objetos (título, autor, quantidade) e funções adicionarLivro(título, autor, quantidade), removerLivro(título), atualizarQuantidade(título, novaQuantidade) e listarLivros(), usando condicionais para verificar existência e laços para iterar. Avalie com base nos seguintes critérios: 70% funcionalidade, 20% legibilidade, 10% comentários."
    ]

    exercise_prompt_mapping = {
        "1": 0, "2": 1, "3": 2, "4": 3, "5": 4, "6": 5, "7": 6, "8": 7, "9": 8
    }

    while True:
        exercicio_num = input("Digite o número do exercício (1 a 9): ")
        if exercicio_num in ["1", "2", "3", "4", "5", "6", "7", "8", "9"]:
            break
        print("Número inválido. Digite um número de 1 a 9.")

    base_link = "https://apps.projetodesenvolve.online/ora-grading/block-v1:ProjetoDesenvolve+JS1+01+type@openassessment+block@"
    driver.get(base_link + {
        "1": "639903f33c5d4e7398c63c56bff74874",
        "2": "b924b6b0080945f1abfcb83838b09887",
        "3": "d6284ec33b89453e8843e30e0a44be09",
        "4": "34753cb38f484778953a265f07175c47",
        "5": "ab53b1623fb14675a6ea6989cbe6f892",
        "6": "cd3688e77c85498e9b9a472b6cdfb381",
        "7": "0a9bb8ca20bc450dbe29d543ea51aa10",
        "8": "b18c2d9230e9428abb9c6c44fa8f2596",
        "9": "b9efe4fda6884d519fa8fec46f1cdb05"
    }[exercicio_num])
    time.sleep(1)

    print("Elementos com ID encontrados:", [e.get_attribute("id") for e in driver.find_elements(By.TAG_NAME, "div") if e.get_attribute("id")])
    print("Elementos com classe encontrados:", [e.get_attribute("class") for e in driver.find_elements(By.TAG_NAME, "div") if e.get_attribute("class")])

    try:
        grading_status_button = wait.until(EC.element_to_be_clickable((By.ID, "multi-dropdown-filter-label-header_gradingStatus-3")))
        grading_status_button.click()
        print(f"Checkbox 'Grading Status' clicado com sucesso para exercício {exercicio_num}.")
    except Exception as e:
        print(f"Falha ao encontrar 'multi-dropdown-filter-label-header_gradingStatus-3': {e}. Tentando alternativa...")
        try:
            grading_status_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'filter-label') and contains(text(), 'Grading Status')]")))
            grading_status_button.click()
            print(f"Checkbox 'Grading Status' clicado com sucesso usando alternativa para exercício {exercicio_num}.")
        except Exception as e:
            print(f"Falha ao clicar em 'Grading Status' para exercício {exercicio_num}: {e}. Pulando esta etapa.")

    time.sleep(1)

    try:
        ungraded_checkbox = wait.until(EC.element_to_be_clickable((By.ID, "checkbox-filter-check-header_gradingStatus-6")))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ungraded_checkbox)
        ungraded_checkbox.click()
        print(f"Checkbox 'Ungraded' marcado com sucesso para exercício {exercicio_num}.")
    except Exception as e:
        print(f"Falha ao marcar o checkbox para exercício {exercicio_num}: {e}. Tentando clique forçado via JavaScript...")
        ungraded_checkbox = wait.until(EC.presence_of_element_located((By.ID, "checkbox-filter-check-header_gradingStatus-6")))
        driver.execute_script("arguments[0].click();", ungraded_checkbox)
        print("Clique forçado via JavaScript executado.")

    time.sleep(1)

    try:
        view_all_responses_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "view-all-responses-btn")))
        view_all_responses_button.click()
        print(f"Botão 'View all responses' clicado com sucesso para exercício {exercicio_num}.")
    except Exception as e:
        print(f"Falha ao clicar em 'View all responses' para exercício {exercicio_num}: {e}. Tentando clique forçado via JavaScript...")
        view_all_responses_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "view-all-responses-btn")))
        driver.execute_script("arguments[0].click();", view_all_responses_button)
        print("Clique forçado via JavaScript executado.")

    time.sleep(1)

    max_attempts = 5
    attempt_count = 0

    while attempt_count < max_attempts:
        try:
            # Tentar localizar links GitHub por texto ou atributo href
            github_elements = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'github.com')] | //*[contains(text(), 'github.com')]")))
            if not github_elements:
                print(f"Nenhum link GitHub encontrado para o aluno atual no exercício {exercicio_num}. Passando para o próximo aluno.")
                raise Exception("Nenhum link encontrado")

            processed_links = 0
            for index, element in enumerate(github_elements, 1):
                github_link_text = element.text.strip() if element.text else element.get_attribute("href")
                print(f"Texto bruto do link GitHub {index} para exercício {exercicio_num}: {github_link_text}")
                # Tentar extrair todos os URLs válidos do texto
                potential_urls = re.findall(r'https?://(?:www\.)?github\.com/[\w-]+/[\w-]+(?:/[\w-]+)*(?:\.js)?', github_link_text)
                if not potential_urls:
                    print(f"Nenhum URL válido extraído do texto '{github_link_text}' para o envio {index} de exercício {exercicio_num}. Pulando este link.")
                    continue

                for github_url in potential_urls:
                    print(f"Acessando link do GitHub {index} para exercício {exercicio_num}: {github_url}")
                    js_code = download_file_content(github_url)
                    print(f"Retorno de download_file_content: {js_code[:50] if js_code else 'Falha'}")
                    if js_code:
                        selected_prompt_index = exercise_prompt_mapping[exercicio_num]
                        selected_prompt = [all_prompts[selected_prompt_index]]
                        nota = evaluate_with_ia(selected_prompt, js_code)
                        if nota is not None:
                            print(f"Nota sugerida pela IA para o envio {index} de exercício {exercicio_num}: {nota}")
                            mark_grade(nota, driver, wait, exercicio_num)
                            processed_links += 1
                        else:
                            print(f"O código enviado não corresponde ao prompt do exercício {exercicio_num}. Pulando este link.")
                    else:
                        print(f"Falha ao baixar o código para o envio {index} de exercício {exercicio_num}. Pulando este link.")
                    time.sleep(1)  # Pausa para evitar avanços rápidos

            if processed_links == 0:
                print("Nenhum link foi processado com sucesso. Passando para o próximo aluno.")
                raise Exception("Nenhum link processado")

            # Tentar clicar no botão de próximo aluno após processar todos os links
            max_click_attempts = 2
            for attempt in range(max_click_attempts):
                try:
                    next_student_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Load next submission')]")))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_student_button)
                    next_student_button.click()
                    print(f"Tentativa {attempt + 1}/{max_click_attempts}: Botão de próximo aluno clicado com sucesso. Avançando para o próximo aluno.")
                    time.sleep(2)  # Aumentar pausa após avanço
                    break
                except Exception as e:
                    print(f"Tentativa {attempt + 1}/{max_click_attempts}: Não foi possível clicar no botão de próximo aluno: {e}")
                    if attempt == max_click_attempts - 1:
                        # Verificar se é o fim após falhar todas as tentativas
                        try:
                            next_student_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Load next submission')]")), 2)
                            if not next_student_button.is_enabled():
                                print("Nenhum aluno restante. Tentando fechar a avaliação.")
                                try:
                                    close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']")), 5)
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
                                    close_button.click()
                                    print("Botão 'Close' clicado com sucesso. Finalizando avaliação.")
                                except Exception as e:
                                    print(f"Falha ao clicar no botão 'Close': {e}. Finalizando sem fechar.")
                                break
                        except:
                            print("Botão de próximo aluno não encontrado. Tentando fechar a avaliação.")
                            try:
                                close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']")), 5)
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
                                close_button.click()
                                print("Botão 'Close' clicado com sucesso. Finalizando avaliação.")
                            except Exception as e:
                                print(f"Falha ao clicar no botão 'Close': {e}. Finalizando sem fechar.")
                            break
                    time.sleep(1)

            attempt_count += 1

        except Exception as e:
            print(f"Erro ao processar aluno atual: {e}. Tentando avançar.")
            # Tentar avançar após falha
            max_click_attempts = 2
            for attempt in range(max_click_attempts):
                try:
                    next_student_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Load next submission')]")))
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_student_button)
                    next_student_button.click()
                    print(f"Tentativa {attempt + 1}/{max_click_attempts}: Botão de próximo aluno clicado com sucesso após falha. Avançando.")
                    time.sleep(2)
                    break
                except Exception as e:
                    print(f"Tentativa {attempt + 1}/{max_click_attempts}: Não foi possível clicar no botão de próximo aluno após falha: {e}")
                    if attempt == max_click_attempts - 1:
                        # Verificar se é o fim após falhar todas as tentativas
                        try:
                            next_student_button = wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(@aria-label, 'Load next submission')]")), 2)
                            if not next_student_button.is_enabled():
                                print("Nenhum aluno restante. Tentando fechar a avaliação.")
                                try:
                                    close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']")), 5)
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
                                    close_button.click()
                                    print("Botão 'Close' clicado com sucesso. Finalizando avaliação.")
                                except Exception as e:
                                    print(f"Falha ao clicar no botão 'Close': {e}. Finalizando sem fechar.")
                                break
                        except:
                            print("Botão de próximo aluno não encontrado. Tentando fechar a avaliação.")
                            try:
                                close_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']")), 5)
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", close_button)
                                close_button.click()
                                print("Botão 'Close' clicado com sucesso. Finalizando avaliação.")
                            except Exception as e:
                                print(f"Falha ao clicar no botão 'Close': {e}. Finalizando sem fechar.")
                            break
                    time.sleep(1)

        except KeyboardInterrupt:
            print("Interrompido manualmente pelo usuário.")
            break

    print(f"Avaliação do exercício {exercicio_num} de JavaScript concluída para todos os alunos.")
    input("Pressione Enter para fechar...")
    driver.quit()

# Função genérica para iniciar o processo de avaliação
def start_evaluation():
    login_to_platform()
    discipline = input("Qual disciplina deseja corrigir? (ex.: javascript): ").lower()
    evaluation_functions = {"javascript": evaluate_javascript}
    if discipline in evaluation_functions:
        evaluation_functions[discipline]()
    else:
        print(f"Disciplina '{discipline}' não suportada. Encerrando...")
        driver.quit()

if __name__ == "__main__":
    start_evaluation()
# Caderno de Aulas de laboratório MC921 - Construção de Compiladores

## O que será necessário para utilizar o caderno:

Vocês vão precisar ter acesso a uma aplicação chamada "Terminal".
Talvez seja a aplicação mais útil, porque vocês poderão usar o mesmo para
dizer ao seu computador que faça praticamente tudo o que vocês quiserem.
Usuários de Mac e Linux provavelmente estão familiarizados com este
aplicativo. No Windows isso é um pouco mais complicado, já que a Microsoft é
um tanto rebelde. Vocês podem instalar um emulador de terminal mais amigável
do que o "Prompt de Comando" ou mesmo o "PowerShell" que acompanham o
Windows. Eu sugiro instalar o [Git Bash](https://git-scm.com/downloads).
Durante a instalação, certifique-se de selecionar a opção "Use Windows'
default console window". Uma outra opção, recomendado principalmente para
quem quer iniciar no mundo Linux, é instalar o Shell Bash do Linux no Windows
através do subsistema Windows para o Linux, presente nas versões mais atuais
do Windows 10.
[Aqui](http://www.techtudo.com.br/dicas-e-tutoriais/noticia/2016/04/como-instalar-e-usar-o-shell-bash-do-linux-no-windows-10.html)
vocês encontrarão um dos muitos tutoriais de como fazer isto.

Para criar um programa, utilizamos um editor de texto para escrever o código
do programa (e.g., [Vim](http://www.vim.org/), [Atom](https://atom.io/)) ou
um IDE -- Ambiente de Desenvolvimento Integrado (e.g.,
[PyCharm](https://www.jetbrains.com/pycharm/),
[WingIDE](http://wingware.com/)) e um compilador/interpretador python. O
compilador é o que transforma o código em um programa executável.  O
interpretador é um programa que executa diretamente os comandos da linguagem.
Será preciso instalar o compilador/interpretador python da versão 3.  Vocês
poderão baixá-lo do site (https://www.python.org/downloads)

## Jupyter Notebook

Um dos avanços mais significativos na arena de computação científica está em
andamento com a explosão de interesse na tecnologia [Jupyter Notebook](jupyter.org).
A publicação científica Nature apresentou recentemente um
artigo sobre os benefícios dos notebooks Jupyter para pesquisas científicas.
Jupyter Notebook nada mais é do que uma aplicação WEB de código aberto que
permite criar e compartilhar documentos que contenham código, equações,
visualizações e texto narrativo.

Depois de fazer o clone (recomendado, mais informações
[aqui](https://tableless.com.br/tudo-que-voce-queria-saber-sobre-git-e-github-mas-tinha-vergonha-de-perguntar/)
ou [aqui](http://rogerdudler.github.io/git-guide/index.pt_BR.html)) ou o
download do caderno de aulas em uma pasta local, vocês precisarão instalar o
Jupyter Notebook e algumas extensões para poder usar o material do curso. Com o
Python3 já instalado na sua máquina, execute no terminal:

  - obs.: Se vc tem somente o python3 instalado em sua máquina, o comando `pip3` pode
não existir. Neste caso, digite apenas `pip`.

```sh
    $ pip3 install jupyter
    $ pip3 install jupyter_contrib_nbextensions
    $ pip3 install tutormagic
    $ jupyter contrib nbextension install --user
```

Para usar as extensões necessárias, você também precisará ativá-las. Para fazer
isso, você pode usar um subcomando Jupyter:

```sh
    $ jupyter nbextension enable codefolding/main
    $ jupyter nbextension enable latex_envs/latex_envs
    $ jupyter nbextension enable python-markdown/main
    $ jupyter nbextension enable toc2/main
```

Depois de instalar o Jupyter Notebook e as extensões em seu computador, você
está pronto para executar o servidor do notebook. Você pode iniciar o servidor
do notebook a partir da linha de comando. Usando o aplicativo Terminal no Mac/Linux ou
prompt de comando no Windows, vá para a pasta onde você baixou o caderno de aulas e execute:

```sh
    $ jupyter notebook
```

Isso imprimirá algumas informações sobre o servidor do notebook em seu
terminal, incluindo o URL do aplicativo da Web (por padrão,
http://localhost:8888) bem como a forma de encerrar o aplicativo:

```sh
    $ jupyter notebook,
    [I 10:31:03.540 NotebookApp] Serving notebooks from local directory: /Users/marcio/Unicamp/MC102/Python/lectures,
    [I 10:31:03.541 NotebookApp] 0 active kernels,
    [I 10:31:03.541 NotebookApp] The Jupyter Notebook is running at:,
    [I 10:31:03.541 NotebookApp] http://localhost:8888/?token=046cfa3064f0b118f56f6ef8859c4ab68d1d202d79445759,
    [I 10:31:03.541 NotebookApp] Use Control-C to stop this server and shut down all kernels (twice to skip confirmation).
```

Em seguida, jupyter abrirá seu navegador da Web padrão para esta URL. Quando o notebook
abrir no seu navegador, você verá o Notebook Dashboard, que mostrará uma lista
dos cadernos no diretório onde o servidor do notebook foi iniciado. Na maioria das vezes,
você deseja iniciar pelo caderno Practical Asects of Compiler Construction.  Muitas vezes,
este será o seu caderno inicial.


## Extras

  - Livro "Practical Vim, second edition - Edit Text at the Speed of Thought" [The Pragmatic Bookshelf](https://pragprog.com/book/dnvim2/practical-vim-second-edition),
  - Livro (online) sobre o editor Atom [Atom Flight Manual](http://flight-manual.atom.io/),
  - Python 3 Official Documentation. (https://docs.python.org/3/). PFS license, GPL-compatible.


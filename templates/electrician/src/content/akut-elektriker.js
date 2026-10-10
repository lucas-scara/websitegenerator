import { asset } from '../business.js'
import { copy } from '../business.js'
export default {
  "path": "/electrical-repairs",
  "title": copy("Reparos elétricos | Your Company"),
  "description": "Converse conosco sobre reparos elétricos para sua casa ou empresa.",
  "h1": "Reparos elétricos",
  "heroImage": asset("/images/panel-testing.jpg"),
  "heroImageAlt": "Serviços elétricos — imagem ilustrativa",
  "heroImages": [
    asset("/images/panel-testing.jpg")
  ],
  "intro": [
    "Planejando reparos elétricos? Conte como é o imóvel e o que você pretende fazer. Podemos conversar sobre os próximos passos."
  ],
  "heroCtas": [
    {
      "label": "Fale sobre seu projeto",
      "href": "/contact"
    }
  ],
  "blocks": [
    {
      "type": "h2",
      "text": "Uma abordagem prática para seu projeto"
    },
    {
      "type": "p",
      "md": "Cada imóvel é diferente. Primeiro, é preciso entender a instalação atual, o uso do espaço e as mudanças desejadas."
    },
    {
      "type": "ul",
      "items": [
        "Descreva o serviço e os problemas observados.",
        "Converse sobre acesso, prazo e resultado esperado.",
        "Peça informações sobre escopo, materiais e orçamento por escrito."
      ]
    },
    {
      "type": "img",
      "src": asset("/images/lamp-detail.jpg"),
      "alt": "Detalhe de luminária — imagem ilustrativa"
    },
    {
      "type": "h2",
      "text": "Planeje os detalhes antes de iniciar"
    },
    {
      "type": "p",
      "md": "Entre em contato para verificar se o serviço atende ao seu imóvel e se é necessária uma avaliação antes do orçamento."
    },
    {
      "type": "faq",
      "items": [
        {
          "q": "Como pedir um orçamento?",
          "a": "Ligue ou envie um e-mail com uma breve descrição do serviço e seus dados de contato."
        },
        {
          "q": "Quanto custa o serviço?",
          "a": "O custo depende do escopo, dos materiais e das condições da instalação. Peça um orçamento para seu caso."
        }
      ]
    },
    {
      "type": "contact"
    }
  ]
}

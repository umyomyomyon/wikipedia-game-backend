steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/wikipedia-game-16fc7/wikipedia-game', '.']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/wikipedia-game-16fc7/wikipedia-game']

  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    args:
      - run
      - deploy
      - wikipedia-game
      - '--image'
      - 'gcr.io/wikipedia-game-16fc7/wikipedia-game'
      - '--platform'
      - 'managed'
      - '--memory'
      - '128Mi'
      - '--region'
      - 'asia-northeast1'
      - '--allow-unauthenticated'
      - '--set-env-vars'
      - 'RTDB_URL=$_RTDB_URL'

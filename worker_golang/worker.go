// worker.go

// Celery Task
func add(a int, b int) int {
	return a + b
}

func main() {
    // create broker and backend
	celeryBroker := gocelery.NewRedisCeleryBroker("redis://localhost:6379")
    celeryBackend := gocelery.NewRedisCeleryBackend("redis://localhost:6379")

    // use AMQP instead
    // celeryBroker := gocelery.NewAMQPCeleryBroker("amqp://")
    // celeryBackend := gocelery.NewAMQPCeleryBackend("amqp://")

	// Configure with 2 celery workers
	celeryClient, _ := gocelery.NewCeleryClient(celeryBroker, celeryBackend, 2)

	// worker.add name reflects "add" task method found in "worker.py"
	celeryClient.Register("worker.add", add)

    // Start Worker - blocking method
	go celeryClient.StartWorker()

    // Wait 30 seconds and stop all workers
	time.Sleep(30 * time.Second)
	celeryClient.StopWorker()
}